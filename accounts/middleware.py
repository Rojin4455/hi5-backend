import jwt
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status

class TokenRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)

        if response:
            return response  

        response = self.get_response(request)

        return self.process_response(request, response)

    def process_request(self, request):
        
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            try:
                jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
                print("Access token is valid")
            except jwt.ExpiredSignatureError:
                print("Access token expired")
                refresh_token = request.headers.get('RefreshToken')
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)
                        request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                        print("New access token is set")
                    except jwt.ExpiredSignatureError:
                        print("Refresh token expired")
                        return Response({'error': 'Refresh token expired'}, status=status.HTTP_403_FORBIDDEN)
                    except Exception as e:
                        print(f"Invalid refresh token: {str(e)}")
                        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    print("in else condition123")
                    return Response({'error': 'Refresh token is missing'}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({'error': 'Invalid access token'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            print("Authorization header is missing or invalid")

    def process_response(self, request, response):
        if hasattr(response, 'render') and callable(response.render):
            response = response.render()

        if 'HTTP_AUTHORIZATION' in request.META:
            response.headers['Authorization'] = request.META['HTTP_AUTHORIZATION']
        
        # if response.content:
        #     response.headers["Content-Length"] = str(len(response.content))

        return response
