from django.urls import path
from .views import *

urlpatterns = [
path('change-status/<int:id>/',NotificatioStatus.as_view())
]