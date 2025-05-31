from django.db import models
from django.utils import timezone
import uuid
from dateutil.relativedelta import relativedelta  # For accurate month handling
from accounts.models import User

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_movie_limit = models.IntegerField()
    valid_days = models.JSONField(default=list)  # ['MON', 'TUE', 'WED', 'THU'] or ['ALL']
    daily_ticket_limit = models.IntegerField()
    max_discount_per_ticket = models.DecimalField(max_digits=10, decimal_places=2)
    max_ticket_price_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    subscription_id = models.UUIDField(default=uuid.uuid4, editable=False)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVE')
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Track upgrade history
    upgraded_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    upgrade_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + relativedelta(months=1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def is_valid(self):
        return self.status == 'ACTIVE' and self.end_date > timezone.now()
    
    def movies_watched_this_month(self):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.ticket_bookings.filter(booking_date__gte=month_start).count()
    
    def can_book_today(self):
        today = timezone.now().date()
        if self.plan.valid_days != ['ALL']:
            weekday = today.strftime('%a').upper()
            if weekday not in self.plan.valid_days:
                return False
        
        tickets_today = self.ticket_bookings.filter(
            booking_date__date=today
        ).count()
        
        return tickets_today < self.plan.daily_ticket_limit
    
    def get_remaining_days(self):
        """Get remaining days in subscription"""
        if self.status != 'ACTIVE':
            return 0
        remaining = (self.end_date.date() - timezone.now().date()).days
        return max(remaining, 0)
    
    def get_usage_stats(self):
        """Get current month usage statistics"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movies_watched = self.movies_watched_this_month()
        
        today_bookings = self.ticket_bookings.filter(
            booking_date__date=timezone.now().date()
        ).count()
        
        return {
            'movies_this_month': movies_watched,
            'monthly_limit': self.plan.monthly_movie_limit,
            'tickets_today': today_bookings,
            'daily_limit': self.plan.daily_ticket_limit,
            'remaining_days': self.get_remaining_days()
        }
class Merchant(models.Model):
    name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    agreement_amount = models.DecimalField(max_digits=10, decimal_places=2)
    campaign_start_date = models.DateTimeField()
    campaign_end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Coupon(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_redemptions = models.IntegerField(default=100)
    current_redemptions = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.merchant.name} - {self.code}"
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.valid_from <= now <= self.valid_until and
            self.current_redemptions < self.max_redemptions and
            self.merchant.is_active
        )

class UserCoupon(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('REDEEMED', 'Redeemed'),
        ('EXPIRED', 'Expired')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='user_coupons')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_date = models.DateTimeField(auto_now_add=True)
    redemption_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'coupon')
    
    def __str__(self):
        return f"{self.user.first_name} - {self.coupon.code}"