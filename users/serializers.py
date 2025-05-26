from rest_framework import serializers
from .models import CustomUser, Address, Profile
#-------------------------------------------------------------------------------------
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