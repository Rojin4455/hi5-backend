from django.urls import path
from .views import *

urlpatterns = [
    path('add-tier-layout/', AddTierLayoutClass.as_view(), name='add-tier-layout'),
    path('edit-seatcount/<int:tier_id>/', EditSeatCountView.as_view(), name='edit-seatcount'),
    path('screen-time/<int:screen_id>/',ScreenTimeView.as_view(), name='screen-time'),
    path('screen-time/add/', ScreenTimeView.as_view(), name='add-screen-time'),
    path('screen-time/remove/', ScreenTimeView.as_view(), name='delete-screen-time'),
    path('add-movie-schedule/',MovieScheduleView.as_view(), name='add-movie-schedule'),
    path('get-movie-schedule/<int:screen_id>/',ShowDetailsView.as_view(), name='get-movie-schedule'),
    path('dated-screen-time/<int:screen_id>/<str:date>/',DatedShowsView.as_view(), name='dated-screen-time'),
     path('set-time/', SetTimeView.as_view(), name='set_time'),
     path('change-schedule/', ChangeEndDateView.as_view()),
     path('delete-schedule/', DeleteScheduleView.as_view()),
    # path('show-screen-details/<int:screen_id>/<str:date>/<str:time>/',ShowScreenDetailsView.as_view(), name="show-screen-details")
]