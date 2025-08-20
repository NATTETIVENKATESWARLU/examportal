from rest_framework.views import APIView
from rest_framework import viewsets # Not used here but kept from original
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication # Kept from original, used by permission_classes implicitly
from rest_framework.generics import UpdateAPIView, RetrieveAPIView # Kept from original
#-------------------------------------------------------------------------------------------------

from drf_social_oauth2.views import ConvertTokenView # Import for social token exchange
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg import openapi # Import for Swagger documentation
CustomUser = get_user_model()
#-------------------------------------------------------------------------------------------------
from .models import (CustomUser, Profile, Address,OTP ) # Import models including OTP
#-------------------------------------------------------------------------------------------------
from .serializers import (
    RegisterSerializer,
    UserProfileAdminSerializer,
    AddressSerializer,
    ProfileSerializer,
    # New serializers
    EmailSerializer,
    VerifyOTPSerializer,
    SetNewPasswordSerializer,
    ChangePasswordSerializer,
    #logout serializer is not needed as JWT handles token invalidation on logout
    LogoutSerializer,
)
from .utils import generate_otp, send_otp_email # Import OTP utilities
from django.utils import timezone # Import timezone
from django.conf import settings # Import settings

#----------------------------------------------------------------------------------
class RegisterView(APIView):
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: "User registered successfully.", 400: "Bad Request"}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Potentially send a welcome email here
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

#-----------------------------------------------------------------------------------

# 🔒 Require JWT
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication] # Explicitly add if not globally set

    @swagger_auto_schema(
        responses={200: UserProfileAdminSerializer(many=False)})
    def get(self, request):
        user = request.user
        user_data = UserProfileAdminSerializer(user).data

        profile, _ = Profile.objects.get_or_create(user=user)
        profile_data = ProfileSerializer(profile).data

        # Handle multiple addresses if your model changes; for now, it's one-to-many, so filter().first() is okay.
        # If it should be OneToOne, change Address model's ForeignKey to OneToOneField.
        address = Address.objects.filter(user=user).order_by('-id').first() # Get the latest if multiple
        address_data = AddressSerializer(address).data if address else {}

        return Response({
            "user": user_data,
            "profile": profile_data,
            "address": address_data
        })
#-------------------------------------------------------------------------------------
class UpdateBasicProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        request_body=UserProfileAdminSerializer, # User can update fields defined in this serializer
        responses={200: UserProfileAdminSerializer(many=False)}
    )
    def put(self, request):
        user = request.user
        # Using partial=True allows for partial updates (PATCH behavior with PUT)
        serializer = UserProfileAdminSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------------------------------------------------
class UpdateProfileDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer(many=False)}
    )
    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------------------------------------------------
class UpdateAddressView(APIView): # This should probably be CreateOrUpdateAddressView
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        request_body=AddressSerializer,
        responses={200: AddressSerializer(many=False), 201: AddressSerializer(many=False)}
    )
    def put(self, request): # Can also be POST if creating a new address each time
        # Assuming a user can have multiple addresses, and this updates/creates one.
        # If a user has only one address, get_or_create is fine.
        # If multiple, you might need an address ID or decide to always update the "primary" or latest.
        # For simplicity, let's assume get_or_create logic for a single address record per user for now,
        # or updating the most recent one. If no address, it creates one.
        address, created = Address.objects.get_or_create(
            user=request.user, 
            defaults=request.data # Pass all data if creating
        )
        
        if created:
            serializer = AddressSerializer(address) # Use the newly created address
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # If address exists, update it
            serializer = AddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------------------------------------------------
# NEW VIEWS FOR PASSWORD MANAGEMENT
#-------------------------------------------------------------------------------------

class RequestPasswordResetView(APIView):
    """
    Request an OTP for password reset.
    Input: {"email": "user@example.com"}
    """
    @swagger_auto_schema(
        request_body=EmailSerializer,
        responses={
            200: "OTP sent successfully.",
            400: "Bad Request (e.g., email not found)",
            500: "Email sending failed"
        }
    )
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email__iexact=email)

            # Invalidate previous active (unverified and not expired) OTPs for this user
            OTP.objects.filter(user=user, is_verified=False, expires_at__gt=timezone.now()).update(
                expires_at=timezone.now() - timezone.timedelta(seconds=1) # Mark as expired
            )
            
            otp_code = generate_otp()
            otp_expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
            expires_at_time = timezone.now() + timezone.timedelta(minutes=otp_expiry_minutes)
            
            OTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at_time)

            user_name = user.first_name if user.first_name else user.username
            if send_otp_email(email, otp_code, user_name=user_name):
                return Response(
                    {"message": f"An OTP has been sent to your email address: {email}. It is valid for {otp_expiry_minutes} minutes."}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Failed to send OTP email. Please try again later or contact support."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#-------------------------------------------------------------------------------------
class VerifyOTPView(APIView):
    """
    Verify the OTP.
    Input: {"email": "user@example.com", "otp_code": "123456"}
    Output: {"message": "OTP verified successfully.", "password_reset_token": "uuid-token"}
    """
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: "OTP verified successfully. You can now reset your password.",
            400: "Bad Request (e.g., invalid OTP, expired OTP)"
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            password_reset_token = serializer.save() # save() now returns the token
            token_expiry_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 10)
            return Response({
                "message": f"OTP verified successfully. Use the provided token to set your new password within {token_expiry_minutes} minutes.",
                "password_reset_token": password_reset_token 
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#-------------------------------------------------------------------------------------

class SetNewPasswordView(APIView):
    """
    Set a new password using the token from OTP verification.
    Input: {"password_reset_token": "uuid-token", "new_password": "...", "confirm_new_password": "..."}
    """
    @swagger_auto_schema(
        request_body=SetNewPasswordSerializer,
        responses={
            200: "Password has been reset successfully.",
            400: "Bad Request (e.g., passwords don't match, token invalid/expired)"
        }
    )
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return Response({"message": "Your password has been reset successfully. Please log in with your new password."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#-------------------------------------------------------------------------------------

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: "Password changed successfully.", 400: "Bad Request"}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#-------------------------------------------------------------------------------------

#logout view is not needed as JWT handles token invalidation on logout

class LogoutView(APIView):
    """
    POST request to logout a user by blacklisting the refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=LogoutSerializer,
        responses={
            205: "Logout successful.",
            400: "Invalid or expired refresh token."
        }
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


#-------------------------------------------------------------------------------------
from django.conf import settings
from rest_framework.test import APIRequestFactory
import jwt
import requests
class CustomSocialLoginView(APIView):
    def post(self, request, *args, **kwargs):
        print("CustomSocialLoginView called with data:", request.data)
        # Validate required fields
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Google access token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify token with Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            params={'access_token': token}
        )

        if google_response.status_code != 200:
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract user data
        user_data = google_response.json()
        email = user_data.get('email')
        if not email:
            return Response(
                {'error': 'Email not provided by Google'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create user
        try:
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': user_data.get('given_name', ''),
                    'last_name': user_data.get('family_name', ''),
                    'is_active': True
                }
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'email': user.email,
                    'id': user.id,
                    'is_new': created
                }
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
