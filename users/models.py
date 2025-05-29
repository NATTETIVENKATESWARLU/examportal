from django.db import models
#-----------------------------------------------------------------------------------------------------------
from django.contrib.auth.models import AbstractUser
#-----------------------------------------------------------------------------------------------------------
from django.utils import timezone
from django.conf import settings # For settings.AUTH_USER_MODEL and OTP_EXPIRY_MINUTES
import uuid
#-----------------------------------------------------------------------------------------------------------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, default='user')  # 'admin', 'user'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    def __str__(self):
        return self.email
#-----------------------------------------------------------------------------------------------------------
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.email} - {self.city}, {self.country}"
#-----------------------------------------------------------------------------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    first_name = models.CharField(max_length=30,null=True, blank=True)
    last_name = models.CharField(max_length=30,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} Profile"
    

#-----------------------------------------------------------------------------------------------------------

# NEW OTP Model
#-----------------------------------------------------------------------------------------------------------
class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField() # Expiry for the OTP code itself
    is_verified = models.BooleanField(default=False) # True if OTP code was successfully verified

    # New fields for the password reset token flow
    password_reset_token = models.UUIDField(null=True, blank=True, unique=True, db_index=True)
    password_reset_token_expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 5))
        super().save(*args, **kwargs)

    def __str__(self):
        status_parts = []
        if self.is_verified:
            status_parts.append("Verified")
        else:
            status_parts.append("Pending")
        if self.password_reset_token:
            status_parts.append("ResetTokenIssued")
        return f"{self.user.email} - {self.otp_code} ({', '.join(status_parts)})"

    def is_otp_still_valid_to_verify(self):
        """Checks if the OTP code itself is still usable for initial verification."""
        return not self.is_verified and timezone.now() < self.expires_at

    def is_password_reset_token_still_valid(self):
        """Checks if the generated password_reset_token is still valid for use."""
        return (
            self.is_verified and # OTP must have been verified first
            self.password_reset_token is not None and
            self.password_reset_token_expires_at is not None and
            timezone.now() < self.password_reset_token_expires_at
        )