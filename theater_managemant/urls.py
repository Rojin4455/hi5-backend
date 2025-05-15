from django.urls import path
from .views import *

urlpatterns = [
    path('add-theater/',AddTheaterView.as_view(),name='add-theater'),
    path('get-theaters/',GetTheaterView.as_view(),name='get-theaters'),
    path("theater-details/<int:theaterId>/", GetTheaterDetailsClass.as_view(), name="theater-details"),
    path("add-screen/<int:theaterId>/",AddScreenClass.as_view(),name="add-theater"),
    path('screen-details/<int:screen_id>/',ScreenDetailsClass.as_view(), name='screen-details'),
    path('add-snack-category/', SnackCategoryClass.as_view()),
    path('get-snack-category/', SnackCategoryClass.as_view()),
    path('owner/add-snack/', OwnerSnacksClass.as_view()),
    path('theater/add-snack/', TheaterSnacksClass.as_view()),
    path('theater/get-snack/<int:theater_id>/', TheaterSnacksClass.as_view()),
    path('theater/get-added-snack/<int:theater_id>/', AddedSnacksClass.as_view()),
    path('update-snack/', UpdateSnackTheater.as_view()),
    path('delete-snack/<int:snack_id>/', UpdateSnackTheater.as_view()),
    path('dashboard-theater/', DashBoardDataView.as_view()),
    path('dashboard-booking/',BookingTrendsAPIView.as_view()),
    path('booking-report/',BookingReportView.as_view())

]
