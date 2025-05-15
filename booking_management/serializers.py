from rest_framework import serializers
from screen_management.models import ShowTime,SeatBooking,MovieSchedule,DailyShow
import datetime
from .models import Booking,BookedTicket,OrderSnack



class SeatLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatBooking
        fields = "__all__"





def check_expiry_month(value):
    if not 1 <= int(value) <= 12:
        raise serializers.ValidationError("Invalid expiry month.")


def check_expiry_year(value):
    today = datetime.datetime.now()
    if not int(value) >= today.year:
        raise serializers.ValidationError("Invalid expiry year.")


def check_cvc(value):
    if not 3 <= len(value) <= 4:
        raise serializers.ValidationError("Invalid cvc number.")


def check_payment_method(value):
    payment_method = value.lower()
    if payment_method not in ["card"]:
        raise serializers.ValidationError("Invalid payment_method.")

class CardInformationSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=150, required=True)
    expiry_month = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_month],
    )
    expiry_year = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_year],
    )
    cvc = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_cvc],
    )


class OrderSnackSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSnack
        fields = "__all__"


class BookedTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookedTicket
        fields = "__all__"



class BookingSerializer(serializers.ModelSerializer):
    book_ticket = BookedTicketSerializer(many=True)
    order_snack = OrderSnackSerializer(many=True)

    class Meta:
        model = Booking
        fields = ['book_ticket','order_snack','payment_status','user','email','phone','total',
                  'theater_name','screen_name','theater_address','booking_id','show_date','show_time',
                  'movie_title','movie_poster','movie_backdrop','genres','is_snacks','qr_code','created_at','id']
        
    



    
