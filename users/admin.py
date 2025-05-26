from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Profile
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
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')}),
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
#-------------------------------------------------------------------------------------
# Register models with admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address)
admin.site.register(Profile)
#-------------------------------------------------------------------------------------