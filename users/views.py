from rest_framework.views import APIView
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import UpdateAPIView, RetrieveAPIView
#-------------------------------------------------------------------------------------------------
from .models import CustomUser, Profile, Address
#-------------------------------------------------------------------------------------------------
from .serializers import (
    RegisterSerializer,
    UserProfileAdminSerializer,
    AddressSerializer,
    ProfileSerializer
)

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
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

#-----------------------------------------------------------------------------------

# 🔒 Require JWT
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: UserProfileAdminSerializer(many=False)})
    def get(self, request):
        user = request.user
        user_data = UserProfileAdminSerializer(user).data

        profile, _ = Profile.objects.get_or_create(user=user)
        profile_data = ProfileSerializer(profile).data

        address = Address.objects.filter(user=user).first()
        address_data = AddressSerializer(address).data if address else {}

        return Response({
            "user": user_data,
            "profile": profile_data,
            "address": address_data
        })
#-------------------------------------------------------------------------------------
class UpdateBasicProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=UserProfileAdminSerializer,
        responses={200: UserProfileAdminSerializer(many=False)}
    )
    def put(self, request):
        user = request.user
        serializer = UserProfileAdminSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------------------------------------------------
class UpdateProfileDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
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
class UpdateAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=AddressSerializer,
        responses={200: AddressSerializer(many=False)}
    )
    def put(self, request):
        address, _ = Address.objects.get_or_create(user=request.user)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------------------------------------------------
















