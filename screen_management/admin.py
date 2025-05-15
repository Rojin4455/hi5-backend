from django.contrib import admin
from .models import ShowTime,DailyShow,MovieSchedule,SeatBooking


admin.site.register(ShowTime)
admin.site.register(DailyShow)
admin.site.register(MovieSchedule)
admin.site.register(SeatBooking)
# Register your models here.
