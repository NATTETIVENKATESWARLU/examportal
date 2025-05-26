from django.urls import path
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    RegisterView,
    UserProfileView,
    UpdateBasicProfileView,
    UpdateProfileDetailsView,
    UpdateAddressView,
)



urlpatterns = [

    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='get_user_profile'),
    path('profile/update/', UpdateBasicProfileView.as_view(), name='update_basic_profile'),
    path('profile/details/', UpdateProfileDetailsView.as_view(), name='update_profile_details'),
    path('address/', UpdateAddressView.as_view(), name='update_address'),

]



