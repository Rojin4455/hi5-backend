# services.py
from django.conf import settings
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from urllib.parse import urlencode
from typing import Dict, Any
import requests
import jwt
from .models import User,UserProfile
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from tempfile import TemporaryFile
from django.core.files.base import ContentFile

GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
LOGIN_URL = f'{settings.BASE_APP_URL}/internal/login'

# Exchange authorization token with access token
def google_get_access_token(code: str, redirect_uri: str) -> str:
    print("ACESSSSSSSSSSSSSSS token: ",redirect_uri)
    data = {
        'code': code,
        'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    if not response.ok:
        print('error response from backend:  ',response)
        raise ValidationError('Could not get access token from Google.')
    
    access_token = response.json()['access_token']

    return access_token

# Get user info from google
def google_get_user_info(access_token: str) -> Dict[str, Any]:
    response = requests.get(
        GOOGLE_USER_INFO_URL,
        params={'access_token': access_token}
    )

    if not response.ok:
        raise ValidationError('Could not get user info from Google.')
    
    return response.json()


def save_image_from_url(url, user_profile_instance):
    try:
        # Download the image
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Create a temporary file
        with TemporaryFile() as img_temp:
            img_temp.write(response.content)
            img_temp.seek(0)  # Reset file pointer to the beginning

            # Save the image to the user's profile
            # user_profile_instance.profile_pic.save(
            #     f"{user_profile_instance.user.id}_profile_pic.jpg",
            #     ContentFile(img_temp.read())
            # )
            
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_user_data(validated_data):
    domain = settings.BASE_API_URL
    redirect_uri = f'{domain}/auth/api/login/google/'

    code = validated_data.get('code')
    error = validated_data.get('error')
    if error or not code:
        params = urlencode({'error': error})
        print("Error here ::::",params)
        
        return redirect(f'{LOGIN_URL}?{params}')
    
    access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
    user_data = google_get_user_info(access_token=access_token)
    print("USEEEEEEr_dataaaaaaaaaaaaaaaa: ",user_data)

    # Creates user in DB if first time login
    user, created = User.objects.get_or_create(
        email=user_data['email'],
        defaults={
            'first_name': user_data['given_name'], 
            'last_name': user_data['family_name']
        }
    )
    print("created userrrrr: ", user.email)


    user_profile,created = UserProfile.objects.get_or_create(
        user=user,  # Pass the user instance here

    )
    picture_url = user_data.get('picture')
    if picture_url and created:
        save_image_from_url(picture_url, user_profile)
    print("user profile created")

    
    
    profile_data = {
        'email': user_data['email'],
        'first_name': user_data.get('given_name'),
        'last_name': user_data.get('family_name'),
    }
    return profile_data