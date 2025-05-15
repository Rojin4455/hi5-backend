from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import SeatBooking

User = get_user_model()

@receiver(pre_delete, sender=User)
def reset_seats_on_user_deletion(sender, instance, **kwargs):
    # Update SeatBooking objects associated with the deleted user
    SeatBooking.objects.filter(user=instance).update(
        user=None,
        status='available'
    )
