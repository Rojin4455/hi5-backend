
from django.urls import path
from .views import *



urlpatterns = [
    path('login/',AdminLogin.as_view(),name='login'),
    path('allusers/',AllUsers.as_view(),name='all-users'),
    path('change-status/<int:user_id>/',ChangeStatus.as_view(),name='change-status'),
    path('owner-details/<int:ownerId>/',GetOwnerDetails.as_view(),name='change-status'),
    path('get-owners/',GetTheaterOwnersView.as_view(),name='all-owners'),
    path('get-requested-owners/',GetRequestedOwnersView.as_view(),name='all-requested-owners'),
    path('theater-owners/<int:owner_id>/approve/', ApproveTheaterOwnerView.as_view(),name='approve-theater-owner'),
    path('theater-owners/<int:owner_id>/disapprove/', DisapproveTheaterOwnerView.as_view(),name='disapprove-theater-owner'),
    path('owner-all-details/<int:id>/', OwnerAllDetailsView.as_view(),name='owner-all-details'),
    path('approve-theater/<int:theaterId>/', ApproveTheaterclass.as_view(), name='approve-theater'),
    path('disapprove-theater/<int:theaterId>/', DisapproveTheaterclass.as_view(), name='disapprove-theater'),
    path('dashboard/', DashBoardDataView.as_view()),
    path('booking-report/',BookingReportView.as_view()),
    path('dashboard-booking/',BookingTrendsAPIView.as_view()),

]