# cookieapp/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from twilio.rest import Client
import cinemato.settings as project_settings
import urllib.parse
from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import RequestOTPSerializer,VerifyOTPSerializer, EditProfileSerializer
from .models import User, OTP, UserProfile as UserImage, UserLocation
from django.core.mail import send_mail
from .services import get_user_data
from django.shortcuts import redirect
from django.conf import settings
from .serializers import AuthSerializer
import jwt
from django.middleware.csrf import get_token
import cloudinary.uploader
import logging
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


def checking_function():
    print("status success")

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    
    return {
        'refresh':str(refresh),
        'access':str(refresh.access_token),
    }
        

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import jwt

class RefreshAccessTokenView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access this view since we're using refresh token
    authentication_classes = []  # Disable authentication for this view

    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({'error': 'Authorization header is missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Expecting format: "Bearer <token>"
        try:
            bearer, refresh_token = auth_header.split(' ')
            if bearer != 'Bearer':
                return Response({'error': 'Invalid token prefix'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Invalid Authorization header format'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use the refresh token to generate a new access token
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            return Response({'access': new_access_token}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Refresh token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("request otp: cookie:   ", request.session.session_key)
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_code = serializer.create_otp(serializer.validated_data)

            # Send OTP via email or SMS based on the provided data
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')

            if email:   
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp_code}. It will expire in 20 seconds.',
                    project_settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
            elif phone:
                print("data is valid")
                try:
                    # Validate required settings
                    required_settings = ['ACCOUNT_SID', 'AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'COUNTRY_CODE']
                    for attr in required_settings:
                        if not hasattr(settings, attr):
                            logger.error(f"Missing required Twilio setting: {attr}")
                            return Response({"message": "Server configuration error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    # Initialize Twilio Client
                    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

                    # Send OTP message
                    message = client.messages.create(
                        body=f'Your OTP is: {otp_code}',
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=f'{settings.COUNTRY_CODE}{phone}'
                    )

                    logger.info(f"OTP sent successfully to {phone}: Message SID {message.sid}")
                    return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)

                except TwilioRestException as e:
                    logger.error(f"Twilio error: {e}")
                    return Response({"message": "Failed to send OTP due to provider error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                except Exception as e:
                    logger.error(f"Unexpected error sending OTP: {e}")
                    return Response({"message": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    print("error: ",serializer.errors)

                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        print("Received Data:", request.data)
        print("cookie:   ", request.session.session_key)
        
        if serializer.is_valid():
            print("Serializer is valid")
            user = serializer.create_user(serializer.validated_data)
            
            if user is not None:
                if user.is_active:
                    
                    
                    refresh = RefreshToken.for_user(user)
                    access = str(refresh.access_token)
                    refresh = str(refresh)

                    response = Response()
                    print("access token in verify otp: ",access)
                    
                    user.status = True

                    csrf_token = get_token(request)
                    response.set_cookie('csrftoken', csrf_token, httponly=True)

                    
                    response.data = {"Success": "Login successfully", "token": {"access":access,"refresh":refresh},'requestData':{"username":user.first_name,"email":user.email,"phone":user.phone}}
                    return response
                else:
                    return Response({"message": "This account is Blocked"}, status=status.HTTP_404_NOT_FOUND)
            else:
                print("User creation failed")
        else:
            print("Serializer errors:", serializer.errors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ResendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
            serializer = RequestOTPSerializer(data=request.data)
            if serializer.is_valid():
                otp_code = serializer.create_otp(serializer.validated_data)

                # Send OTP via email or SMS based on the provided data
                email = serializer.validated_data.get('email')
                phone = serializer.validated_data.get('phone')

                if email:
                    send_mail(
                        'Cinemato - Your OTP Code',
                        f'Your OTP code is {otp_code}',
                        project_settings.DEFAULT_FROM_EMAIL,
                        [email],
                    )
                elif phone:
                    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
                    message = client.messages.create(
                        body=f'Your OTP is: {otp_code}',
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=f'{settings.COUNTRY_CODE}{phone}'
                    )
                print("success")
                return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmGoogleLogin(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_data, *args, **kwargs):
        try:
            user = User.objects.get(email=user_data['email'])
            if user.is_active:
                return Response({"user_id": user.id}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "This account is not active!"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)


# views that handle 'localhost://8000/auth/api/login/google/'
class GoogleLoginApi(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        auth_serializer = AuthSerializer(data=request.GET)
        auth_serializer.is_valid(raise_exception=True)

        validated_data = auth_serializer.validated_data
        user_data = get_user_data(validated_data)

        if 'email' in user_data:
            mock_request = request._request
            confirm_view = ConfirmGoogleLogin.as_view()

            response = confirm_view(mock_request, user_data=user_data)

            if response.status_code == status.HTTP_200_OK:
                user_id = response.data.get('user_id')
                user = User.objects.get(id=user_id)
                

                custom_data = {
                    'user_id': user.id,
                    'email': user.email
                }


                query_string = urllib.parse.urlencode(custom_data)
                print("_________________________________________________________________")

                print(f'Redirect URL: {settings.BASE_APP_URL}/?{query_string}')
                return redirect(f'{settings.BASE_APP_URL}/?data={query_string}')
            else:
                return response

        return Response({"Error": "Email is not in the user data object"}, status=status.HTTP_404_NOT_FOUND)
        


class SetToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = User.objects.get(id = request.data['user_id'])
        # data = get_tokens_for_user(user)
        response = Response(status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh = str(refresh)
        user.status = True
    
        response.data = {"Success": "Token set to cookie successfully", 'requestData': {"email":user.email},'token':{'refresh':refresh,'access':access}, "status":status.HTTP_200_OK}
        return response





class UserProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        user_obj = User.objects.get(id=user_id)
        user_profile = None
        try:
            user_profile = UserImage.objects.get(user=user_obj)
        except UserImage.DoesNotExist:
            pass

        user_details = {
            'email': user_obj.email,
            'profile': user_profile.image_url if user_profile else None
        }
        

        return Response({"message": "test is working", "user_details": user_details}, status=status.HTTP_200_OK)

    

class UserLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        user = request.user
        user.status = False
        user.save()
        try:
            refresh_token = request.data.get("refresh_token")

            # If a refresh token exists, blacklist it
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Something went wrong during logout"}, status=status.HTTP_400_BAD_REQUEST)
        # return Response({"detail": "Logout successful."}, status=200)



class UpdateUserProfile(APIView):

    permission_classes = [IsAuthenticated]

    def put(self,request):
        user = request.user
        profile_pic = request.FILES.get("profile_pic")

        if profile_pic:
            print("profile pic",profile_pic)
            user_image,created = UserImage.objects.get_or_create(user = user)
            # user_image.profile_pic = profile_pic


            upload_result = cloudinary.uploader.upload(
                profile_pic,
                folder="user_photos"
            )
            
            image_url = upload_result.get('secure_url')

            user_image.image_url = image_url
            user_image.save()

            return Response({"message":"Profile Photo Updated Successfully","profilePhoto":user_image.image_url},status=status.HTTP_200_OK)
        return Response({"error": "No profile picture provided"}, status=status.HTTP_400_BAD_REQUEST)
    



class EditUserProfile(APIView):

    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        serializer = EditProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()


        data = {
            "phone":user.phone,
            "email":user.email,
            "username":user.first_name
        }

        return Response({"message":"User profile details Updated Successfully","updatedData":data},status=status.HTTP_200_OK)
    


class UpdateUserLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        data = request.data
        user = request.user
        address = data['address']
        lat = data['lat']
        lng = data['lng']
        try:
            user_location = UserLocation.objects.get(user=user)
        except:
            user_location = UserLocation.objects.create(user=user,lat=lat,lng=lng)
            return Response({"message":"User location details Updated Successfully",},status=status.HTTP_200_OK)

        user_location.lat = lat
        user_location.lng = lng
        user_location.location = address
        user_location.save()
        return Response({"message":"User location details Updated Successfully",},status=status.HTTP_200_OK)

        

        