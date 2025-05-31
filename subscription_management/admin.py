from django.contrib import admin
from subscription_management.models import Plan,Subscription,Merchant,Coupon,UserCoupon

admin.site.register(Plan)
admin.site.register(Subscription)
admin.site.register(Merchant)
admin.site.register(Coupon)
admin.site.register(UserCoupon)

# Register your models here.
