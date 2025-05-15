from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', OwnerSignupView.as_view(),name='owner-signup'),
    path('login/', OwnerLoginView.as_view(),name='owner-login'),
    path('logout/', OwnerLogoutView.as_view(),name='owner-logout'),
    path('owner-details/<int:notificationId>/',OwnerDetailsView.as_view()),
]

