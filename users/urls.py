from django.urls import path
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    RegisterView,
    UserProfileView,
    UpdateBasicProfileView,
    UpdateProfileDetailsView,
    UpdateAddressView,
    ChangePasswordView,
    RequestPasswordResetView,
    VerifyOTPView,
    SetNewPasswordView,
    LogoutView,
)



urlpatterns = [

    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='get_user_profile'),
    path('profile/update/', UpdateBasicProfileView.as_view(), name='update_basic_profile'),
    path('profile/details/', UpdateProfileDetailsView.as_view(), name='update_profile_details'),
    path('address/', UpdateAddressView.as_view(), name='update_address'),
    # New Password Management URLs
    path('auth/password/change/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/password/reset/request/', RequestPasswordResetView.as_view(), name='request_password_reset_otp'),
    path('auth/password/reset/verify-otp/', VerifyOTPView.as_view(), name='verify_otp_password_reset'),
    path('auth/password/reset/confirm/', SetNewPasswordView.as_view(), name='set_new_password_after_otp'),# Renamed 'set-new' to 'confirm' for clarity
    path('auth/logout/', LogoutView.as_view(), name='logout'),


]



