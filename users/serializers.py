from rest_framework import serializers
from .models import CustomUser, Address, Profile, OTP
#-------------------------------------------------------------------------------------
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings # Import settings
import uuid

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'phone_number',
            'password', 'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(**validated_data)
        return user

#-------------------------------------------------------------------------------------
class UserProfileAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number','role']


#-------------------------------------------------------------------------------------


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'first_name', 'last_name', 'date_of_birth']

#-------------------------------------------------------------------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['country', 'city', 'postal_code']

#-------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------
# NEW SERIALIZERS FOR PASSWORD MANAGEMENT
#-------------------------------------------------------------------------------------



class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email__iexact=value).exists(): # Case-insensitive email check
            raise serializers.ValidationError("User with this email address does not exist.")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField() # Email is still needed to find the user and their OTP
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        # Find the latest, unverified, non-expired OTP for this user
        otp_instance = OTP.objects.filter(
            user=user, 
            otp_code=otp_code, 
            is_verified=False, # Must not have been verified yet
            expires_at__gt=timezone.now() # Must not be expired
        ).order_by('-created_at').first()

        if not otp_instance:
            raise serializers.ValidationError({"otp_code": "Invalid OTP, it may have expired, or already been used."})
        
        # The check `expires_at__gt=timezone.now()` already handles expiry.
        # if timezone.now() > otp_instance.expires_at:
        #     raise serializers.ValidationError({"otp_code": "OTP has expired. Please request a new one."})
        
        attrs['otp_instance'] = otp_instance
        # attrs['user'] = user # user is on otp_instance.user
        return attrs

    def save(self):
        otp_instance = self.validated_data['otp_instance']
        
        # Mark OTP as verified
        otp_instance.is_verified = True
        
        # Generate and store the password reset token
        otp_instance.password_reset_token = uuid.uuid4()
        otp_instance.password_reset_token_expires_at = timezone.now() + timezone.timedelta(
            minutes=getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 10)
        )
        otp_instance.save(update_fields=['is_verified', 'password_reset_token', 'password_reset_token_expires_at'])
        
        return otp_instance.password_reset_token # Return the generated token


class SetNewPasswordSerializer(serializers.Serializer):
    # email and otp_code are removed from here
    password_reset_token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        token = attrs.get('password_reset_token')
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        
        try:
            # Find the OTP instance using the provided token
            otp_instance = OTP.objects.get(password_reset_token=token)
        except OTP.DoesNotExist:
            raise serializers.ValidationError({"password_reset_token": "Invalid or expired password reset token."})

        # Check if the token is still valid for password reset using the model method
        if not otp_instance.is_password_reset_token_still_valid():
            raise serializers.ValidationError({"password_reset_token": "Password reset token has expired or is invalid. Please request a new OTP."})
            
        user = otp_instance.user
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
            
        attrs['user'] = user
        attrs['otp_instance'] = otp_instance # To delete/invalidate it after use
        return attrs

    def save(self):
        user = self.validated_data['user']
        otp_instance = self.validated_data['otp_instance'] # The OTP object that holds the valid token
        new_password = self.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        # Invalidate/delete the OTP instance (and thus the token) after successful password reset
        # Alternatively, you could just nullify the password_reset_token fields
        otp_instance.delete() 
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your old password was entered incorrectly. Please enter it again.")
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        
        user = self.context['request'].user
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        return attrs

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user