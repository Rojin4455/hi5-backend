from django.contrib import admin
from .models import Booking, BookedTicket, OrderSnack

admin.site.register(Booking)
admin.site.register(BookedTicket)
admin.site.register(OrderSnack)

# Register your models here.
