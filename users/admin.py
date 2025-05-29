
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Profile, OTP
#-------------------------------------------------------------------------------------
# Inline for Address (Many-to-One)
class AddressInline(admin.TabularInline):
    model = Address
    extra = 0  # No extra empty forms

# Inline for Profile (One-to-One)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
#-------------------------------------------------------------------------------------
# Custom User Admin with Inlines
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    inlines = [ProfileInline, AddressInline]

    list_display = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),  # ❌ 'date_of_birth' removed
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role', {'fields': ('role',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'role'),
        }),
    )

#otp admin class
@admin.register(OTP) # Using the decorator is a common way
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'expires_at', 'is_verified')
    search_fields = ('user__email', 'otp_code')
    list_filter = ('is_verified', 'created_at') # Added 'created_at' as an example filter
    readonly_fields = ('user', 'otp_code', 'created_at', 'expires_at', 'is_verified') # Make all fields read-only if change is disabled

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Return False to prevent any changes.
        # Even if you allow changes for superusers, it's usually better to handle OTP state via application logic.
        return False 

    def has_delete_permission(self, request, obj=None):
        # Optionally, prevent deletion too if OTPs are for audit.
        # return False
        return super().has_delete_permission(request, obj) # Default behavior (allows if user has permission)

#-------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------
# Register models with admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address)
admin.site.register(Profile)
#-------------------------------------------------------------------------------------