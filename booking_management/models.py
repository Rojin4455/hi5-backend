from django.db import models
from accounts.models import User
from datetime import datetime
import uuid
import qrcode
from io import BytesIO
import cloudinary.uploader




class Booking(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    payment_status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user                        = models.ForeignKey(User, null=True, blank=True, related_name='booking', on_delete=models.CASCADE)
    email                       = models.EmailField(null=True, blank=True)
    phone                       = models.CharField(max_length=10, null=True, blank=True)
    total                       = models.DecimalField(max_digits=6, decimal_places=2)
    theater_id                  = models.BigIntegerField()
    screen_id                   = models.BigIntegerField()
    theater_name                = models.TextField()
    screen_name                 = models.CharField()
    theater_address             = models.TextField()
    booking_id                  = models.CharField(max_length=150,null=True)
    show_date                   = models.DateField()
    show_time                   = models.TimeField()
    movie_title                 = models.CharField(max_length=150)
    movie_poster                = models.URLField(max_length=500, blank=True, null=True)
    movie_backdrop              = models.URLField(max_length=500, blank=True, null=True)
    genres                      = models.CharField(max_length=200, null=True, blank=True)
    is_snacks                   = models.BooleanField(default=False)
    qr_code                     = models.URLField(blank=True, null=True)
    stripe_checkout_session_id  = models.CharField(max_length=255, blank=True, null=True)
    created_at                  = models.DateTimeField(auto_now_add=True)
    updated_at                  = models.DateTimeField(auto_now=True)
    is_cancelled                = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            today = datetime.now().strftime('%Y%m%d')
            self.booking_id = f"BOOK-{today}-{uuid.uuid4().hex[:4].upper()}"
        if self.payment_status == 'success' and not self.qr_code:
            qr_data = {
                'booking_id': self.booking_id,
                'movie_title': self.movie_title,
                'show_date': self.show_date.isoformat(),
                'show_time': self.show_time.isoformat(),
                'theater_name': self.theater_name,
                'screen_name': self.screen_name,
                'total': str(self.total),
            }
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            response = cloudinary.uploader.upload(buffer, folder="qr_codes", public_id=self.booking_id)
            self.qr_code = response.get("secure_url")
            
            buffer.close()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.movie_title} in {self.theater_name} at {self.show_date} - {self.show_time} {self.payment_status}"



class BookedTicket(models.Model):
    booking         = models.ForeignKey(Booking, related_name='book_ticket', on_delete=models.CASCADE)
    seat_identifier = models.CharField(max_length=10)
    seat_id         = models.IntegerField()
    price           = models.DecimalField(max_digits=6, decimal_places=2)
    tier_name       = models.CharField(max_length=100)

    def __str__(self):
        return f"seat {self.seat_identifier} in {self.booking.theater_name} {self.booking.screen_name} "


class OrderSnack(models.Model):
    booking         = models.ForeignKey(Booking, related_name='order_snack', on_delete=models.CASCADE)
    item_name       = models.CharField(max_length=100)
    description     = models.TextField(null=True, blank=True)
    quantity        = models.IntegerField()
    image_url       = models.URLField()
    price           = models.CharField(max_length=10)
    snack_id        = models.IntegerField()
    is_vegetarian   = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

