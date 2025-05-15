from django.contrib import admin
from .models import Screen,Theater,Tier,ScreenImage,Seat,SnackCategory,SnackItem,TheaterSnack



admin.site.register(Screen)
admin.site.register(Theater)
admin.site.register(Tier)
admin.site.register(ScreenImage)
admin.site.register(Seat)
admin.site.register(SnackItem)
admin.site.register(SnackCategory)
admin.site.register(TheaterSnack)
# Register your models here.
