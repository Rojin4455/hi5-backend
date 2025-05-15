from django.urls import path
from .views import RequestOTPView,VerifyOTPView,ResendOtpView,GoogleLoginApi,ConfirmGoogleLogin,SetToken,UserProfile,UserLogout,UpdateUserProfile,EditUserProfile,RefreshAccessTokenView,UpdateUserLocationView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOtpView.as_view(), name='verify-otp'),
    path("auth/api/login/google/", GoogleLoginApi.as_view(), name="login-with-google"),
    path("confirm-google-login/",ConfirmGoogleLogin.as_view(), name="confirm-google-login"),
    path("set-token/",SetToken.as_view(), name="set-token"),
    path("user-profile/",UserProfile.as_view(), name="user-profile"),
    path("user-logout/",UserLogout.as_view(), name="user-logout"),
    path("user/update-profile/",UpdateUserProfile.as_view(), name="user-update-profile"),
    path("user/edit-profile/",EditUserProfile.as_view(), name="user-edit-profile"),
    path("user/logout/",UserLogout.as_view(), name="user-edit-profile"),
    path("renew-token/",RefreshAccessTokenView.as_view(), name='renew-view'),
    path('update-location/', UpdateUserLocationView.as_view(), name='update-location')
]