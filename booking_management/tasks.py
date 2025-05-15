from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from screen_management.models import SeatBooking

@shared_task
def revert_unconfirmed_reservations():
    time_threshold = timezone.now() - timedelta(minutes=1)
    expired_seats = SeatBooking.objects.filter(status='reserved', reserved_at__lt=time_threshold)
    print("function called")
    print("expired seatsssss :", expired_seats)
    for seat in expired_seats:
        seat.status = 'available'
        seat.reserved_at = None
        seat.save()
