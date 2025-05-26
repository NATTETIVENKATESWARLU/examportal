from django.db import models
#-----------------------------------------------------------------------------------------------------------
from django.contrib.auth.models import AbstractUser
#-----------------------------------------------------------------------------------------------------------

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, default='user')  # 'admin', 'user'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    def __str__(self):
        return self.email
    
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.email} - {self.city}, {self.country}"
    
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    first_name = models.CharField(max_length=30,null=True, blank=True)
    last_name = models.CharField(max_length=30,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} Profile"