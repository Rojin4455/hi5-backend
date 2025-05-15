# cookieapp/authenticate.py
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from django.conf import settings
# from django.middleware.csrf import CsrfViewMiddleware
# from rest_framework import exceptions

# def enforce_csrf(request):
#     # Create a CsrfViewMiddleware instance
#     csrf_middleware = CsrfViewMiddleware(get_response=lambda request: None)
#     csrf_middleware.process_request(request)
#     reason = csrf_middleware.process_view(request, None, (), {})
#     print("TTTTTTTTTTTTTTTT",reason)
#     if reason:
#         raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')

# class CustomAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         # Skip authentication for specific paths
#         if request.path in ['/request-otp/']:
#             return None  # Skip authentication for this endpoint

#         # Existing authentication logic
#         header = self.get_header(request)
#         if header is None:
#             raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
#             print("hererererererere",request.COOKIES)
#         else:
#             raw_token = self.get_raw_token(header)

#         if raw_token is None:
#             return None

#         validated_token = self.get_validated_token(raw_token)
#         enforce_csrf(request)  # Enforce CSRF check
#         return self.get_user(validated_token), validated_token


# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# import jwt
# from django.conf import settings
# # from django.contrib.auth.models import User
# from accounts.models import User

# class CustomJWTAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         # Extract the JWT token from the Authorization header
#         auth_header = request.headers.get('Authorization')
        
#         if not auth_header or not auth_header.startswith('Bearer '):
#             return None  # No token or wrong format, skip authentication

#         token = auth_header.split('Bearer ')[1]
        
#         try:
#             # Decode the JWT token
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
#             print("Decoded payload:", payload)

#         except jwt.ExpiredSignatureError:
#             raise AuthenticationFailed('Token has expired')
#         except jwt.InvalidTokenError:
#             raise AuthenticationFailed('Invalid token')

#         try:
#             # Extract user ID from the payload and get the corresponding user
#             print("FWW")
#             user_id = payload.get('user_id')
#             print("user_id: ",user_id)
#             user = User.objects.get(id=user_id)
#             print("user found: ",user)

#         except User.DoesNotExist:
#             raise AuthenticationFailed('User not found123')

#         return (user, None)  # Return the authenticated user

