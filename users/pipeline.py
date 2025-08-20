from users.models import Profile, Address
from social_core.pipeline.partial import partial

# def create_profile(backend, user, response, *args, **kwargs):
#     if not hasattr(user, 'profile'):
#         first_name = response.get('given_name') or response.get('first_name')
#         last_name = response.get('family_name') or response.get('last_name')
#         picture_url = response.get('picture')

#         Profile.objects.create(
#             user=user,
#             first_name=first_name,
#             last_name=last_name,
#             bio="",
#             # To actually store the profile picture, you need to download and save it to ImageField
#         )

# def create_default_address(backend, user, response, *args, **kwargs):
#     if not Address.objects.filter(user=user).exists():
#         Address.objects.create(
#             user=user,
#             country="Unknown",
#             city="Unknown",
#             postal_code="000000"
#         )

def create_profile(backend, user, response, *args, **kwargs):
    if not hasattr(user, 'profile'):
        profile_data = {
            'user': user,
            'first_name': response.get('given_name') or user.first_name or '',
            'last_name': response.get('family_name') or user.last_name or '',
            'bio': ''
        }
        
        if response.get('picture'):
            # Implement your image downloading logic here
            pass
            
        Profile.objects.create(**profile_data)

def create_default_address(backend, user, response, *args, **kwargs):
    if not Address.objects.filter(user=user).exists():
        Address.objects.create(
            user=user,
            country=response.get('locale', 'Unknown').split('_')[-1] if response.get('locale') else 'Unknown',
            city='Unknown',
            postal_code='000000'
        )