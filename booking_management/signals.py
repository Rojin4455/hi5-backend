from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Booking, BookedTicket, OrderSnack
import cinemato.settings as project_settings
from urllib.parse import urlencode
from django.conf import settings



@receiver(post_save, sender=Booking)
def send_booking_confirmation_email(sender, instance, created, **kwargs):
    if instance.payment_status == 'success'  and not instance.is_cancelled: 
        seats = BookedTicket.objects.filter(booking=instance).values_list('seat_identifier', flat=True)
        seats_obj = BookedTicket.objects.filter(booking=instance)
        snacks = OrderSnack.objects.filter(booking=instance)
        seat_list = ', '.join(seats)

        # Generate cancellation URL
        domain = settings.BASE_APP_URL
        frontend_base_url = f"{domain}/user/cancel-unknown-ticket"
        if instance.user:
            cancellation_params = {
                "booking_id": instance.booking_id,
                "id" : instance.id,
                "user_id": instance.user.id,
            }
        else:
            cancellation_params = {
                "booking_id": instance.booking_id,
                "email": instance.email,
            }
        cancellation_url = f"{frontend_base_url}?{urlencode(cancellation_params)}"

        warning_message = (
            "Please note: Once the booking is canceled, it cannot be reversed. "
            "If you proceed with cancellation, your tickets will be made available for others to purchase."
        )

        # Email subject and recipients
        subject = f"Booking Confirmation for {instance.movie_title}"
        to_email = [instance.email]

        # HTML content for email
        html_content = render_to_string('emails/booking_success.html', {
            "movie": {
                "poster_path": instance.movie_poster,
                "title": instance.movie_title,
                "genres": instance.genres.split(", ") if instance.genres else [],
            },
            "selectedTheater": {
                "name": instance.theater_name,
            },
            "formattedDate": instance.show_date.strftime("%d %B, %Y"),
            "selectedTimeOg": instance.show_time.strftime("%I:%M %p"),
            "selectedScreen": instance.screen_name,
            "seatIdentifiers": seat_list,
            "ticketTotal": sum(int(seat.price) for seat in seats_obj),
            "snackTotal": sum(int(snack.price[:-3]) * int(snack.quantity) for snack in snacks),
            "total": instance.total,
            "QrCodeUrl": instance.qr_code,
            "BookingId": instance.booking_id,
            "warning_message": warning_message,
            "cancellation_url": cancellation_url,
        })

        # Plain text body
        email_body = (
            f"Your booking was successful!\n\n"
            f"Warning: {warning_message}\n\n"
            f"To cancel your booking, click the link below:\n"
            f"{cancellation_url}\n\n"
            f"Enjoy your movie!"
        )

        # Debug email body
        print("Email body:\n", email_body)

        # Sending email
        email = EmailMultiAlternatives(
            subject=subject,
            from_email=project_settings.DEFAULT_FROM_EMAIL,
            to=to_email,
        )
        email.attach_alternative(html_content, "text/html")  # Attach HTML content
        email.send()
