from django.urls import path
from .views import *


urlpatterns = [
    path('seat-layout/',SeatLayoutClass.as_view(), name="seat-layout"),
    path('add-selected-seats/', SeleacedSeatsClass.as_view()),
    path('get-added-snack/<int:theater_id>/',AddedSnacksClass.as_view()),
    # path('v1/financial_connections/sessions/', PaymentAPI.as_view(), name='make_payment'),
    path('payment-success/<int:booking_id>/', PaymentSuccessClass.as_view(), name='make_payment'),
    path('payment-cancel/<int:booking_id>/', PaymentCancelClass.as_view(), name='make_payment'),
    path('create-payment-intent/', create_payment_intent, name='create_payment_intent'),
    path('ticket-details/<int:booking_id>/', TicketDetailsClass.as_view(), name='ticket-details'),
    path('booked-tickets/<str:ticket_mode>/', BookedTicketsView.as_view()),
    path('cancel-ticket/', CancelTicketView.as_view() ),
    path('cancel-ticket-unknown/', CancelTicketUnknownView.as_view()),
    path('owner-book-seats/', OwnerBookTicketsView.as_view())

]