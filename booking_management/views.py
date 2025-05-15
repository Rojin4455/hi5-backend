from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from theater_managemant.models import Theater, Screen
from screen_management.models import ShowTime,MovieSchedule,DailyShow,SeatBooking
from .serializers import SeatLayoutSerializer
from collections import defaultdict
from theater_managemant.models import TheaterSnack
from theater_managemant.serializers import TheaterFullSnacksSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .serializers import CardInformationSerializer,BookingSerializer
import stripe
import cinemato.settings as settings
from .models import Booking, BookedTicket, OrderSnack
from rest_framework.decorators import api_view
from datetime import datetime, timezone as datetime_timezone, timedelta
from django.db import transaction
from django.http import HttpResponseRedirect
import calendar
from rest_framework.permissions import AllowAny, IsAuthenticated
import qrcode
from io import BytesIO
import cloudinary.uploader
from django.db.models import Q
from decimal import Decimal
from accounts.models import User







def get_payment_intent_id(checkout_session_id):
    try:
        checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)
        return checkout_session.payment_intent
    except stripe.error.StripeError as e:
        print(f"Failed to retrieve checkout session: {e.user_message}")
        return None
    


def month_converter(month):
    monthMap = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5,"Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10,"Nov": 11, "Dec": 12}


    return monthMap[month]

def digit_month_converter(month):
    monthMap = { 1:"Jan",  2:"Feb",  3:"Mar",  4:"Apr",  5:"May", 6:"Jun",  7:"Jul",  8:"Aug",  9:"Sep",  10:"Oct", 11:"Nov",  12:"Dec"}

class SeatLayoutClass(APIView):
    permission_classes = []

    def post(self, request):
        theater_id = request.data.get('theater_id')
        screen_name = request.data.get('screen_name')
        screen_time = request.data.get('screen_time')
        show_date = request.data.get('date')
        movie_id = request.data.get('movie_id')
        screen_id = request.data.get('screen_id')
        




        if isinstance(show_date, dict):
            show_date = f"{show_date['year']}-{month_converter(show_date['month'])}-{show_date['date']}"

        if not all([theater_id, screen_name,screen_id, screen_time, show_date]):
            return Response(
                {"error": "Missing required fields: theater_id, screen_name, screen_time, date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            theater = Theater.objects.get(id=theater_id)
            
            # screen = Screen.objects.get(theater=theater, name__iexact=screen_name)
            screen = Screen.objects.get(id=screen_id)
            
            time = ShowTime.objects.get(screen=screen, start_time=screen_time)

            movie_schedule = MovieSchedule.objects.get(showtime=time, showtime__screen__theater__id = theater.id, showtime__screen = screen, start_date__lte=show_date, end_date__gte=show_date)

            daily_show = DailyShow.objects.get(schedule=movie_schedule, show_date =  show_date, show_time = screen_time)
            seats = SeatBooking.objects.filter(daily_show=daily_show).order_by('position', 'identifier')
            
            grouped_seats = defaultdict(list)
            for seat in seats:
                data = SeatLayoutSerializer(seat).data
                grouped_seats[seat.position].append(data)

        except Theater.DoesNotExist:
            return Response(
                {"error": f"Theater with id {theater_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Screen.DoesNotExist:
            return Response(
                {"error": f"Screen '{screen_name}' not found in theater with id {theater_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ShowTime.DoesNotExist:
            return Response(
                {"error": f"ShowTime with start time '{screen_time}' not found for screen '{screen_name}'."},
                status=status.HTTP_404_NOT_FOUND
            )
        except MovieSchedule.DoesNotExist:
            return Response(
                {"error": "Movie schedule not found for the specified showtime."},
                status=status.HTTP_404_NOT_FOUND
            )
        except DailyShow.DoesNotExist:
            return Response(
                {"error": f"No daily show found on date '{show_date}' for the specified schedule."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(data=grouped_seats, status=status.HTTP_200_OK)
    


class SeleacedSeatsClass(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        selected_theater = request.data.get("selected_theater")
        selected_seats = request.data.get("selected_seats")
        selected_date = request.data.get("selected_date")
        selected_time = request.data.get("selected_time")
        screen_name = request.data.get("screen_name")
        tier_name = request.data.get("tier")
        seat_layout = request.data.get("seat_layout")
        
        # print("selected theater : ",selected_theater)
        # print("selected selected_seats : ",selected_seats)
        # print("selected selected_date : ",selected_date)
        # print("selected selected_time : ",selected_time)
        # print("selected screen : ",screen_name)

        
        daily_show = get_object_or_404(DailyShow, schedule__showtime__screen__name = screen_name, show_date=str(selected_date['year']) + '-' + str(month_converter(selected_date['month'])) + '-' + str(selected_date['day']), show_time = selected_time)
        identifiers = []
        for seat in selected_seats:
            identifiers.append(seat['identifier'])

        if daily_show:
            seats = SeatBooking.objects.filter(daily_show = daily_show, identifier__in = identifiers)

            for seat in seats:
                if seat_layout:
                    if seat.status == 'available':
                        seat.status = 'reserved'
                        seat.reserved_at = timezone.now()
                        seat.save()
                    else:
                        return Response({"detail": "Seat is already reserved or booked."}, status=status.HTTP_409_CONFLICT)

                else:
                    if seat.status == 'reserved':
                        seat.status ='available'
                        seat.reserved_at = None
                        seat.save()
                    else:
                        return Response({'detail':'seat is already booked'}, status=status.HTTP_409_CONFLICT)

                          
        
        return Response(status=status.HTTP_200_OK)



class AddedSnacksClass(APIView):
    permission_classes = []

    def get(self,request,theater_id):
        theater = Theater.objects.get(id=theater_id)
        existing_snacks = TheaterSnack.objects.filter(theater=theater, stock__gt = 0)
        serializer = TheaterFullSnacksSerializer(existing_snacks, many=True)
        # added_snacks = SnackItem.objects.filter(theater_snack_items__in=existing_snacks)
        # available_categories = SnackCategory.objects.filter(snack_items__in=added_snacks).distinct()
        # serializer = SnackCategorySerializer(available_categories, many=True, context={'snacks': added_snacks})

        return Response({"message":"All categories fetched successfully in theater added snacks", "data":serializer.data}, status=status.HTTP_200_OK)
    







# class PaymentAPI(APIView):
#     def post(self, request):
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         checkout_sessions = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=[
#                 {
#                     'price':"price_1QKxpWIot8iAcc3iHPab8iLt",
#                     'quantity':1
#                 },
#             ],
#             mode='payment',
#             customer_creation='always',
#             success_url="localhost:8000/booking/success/",
#             cancel_url="localhost:8000/booking/cancel/"

#         )
#         print("checkout payment")

#         Response()


@api_view(['POST'])
def create_payment_intent(request):
    data = request.data
    try:
        with transaction.atomic():
            user = request.user if request.user.is_authenticated else None
            selected_time = data['selectedTime']
            selected_date = data['selectedDate']
            theater = data['selectedTheater']
            screen_name = data['selectedScreen']
            selected_seats = data['selectedSeats']
            added_snacks = data['addedSnacks']
            selected_movie = data['selectedMovie']
            total = sum(float(seat['seat']['tier_price']) for seat in selected_seats) + \
                    sum(float(snack['price']) * data['quantities'][str(snack['id'])] for snack in added_snacks)
            theater_obj = Theater.objects.get(id=theater['id'])
            try:
                user = User.objects.get(email=data.get('email'))
            except:
                pass
            screen = Screen.objects.get(theater__id=theater_obj.id, name__iexact=screen_name)
            booking = Booking.objects.create(
                user=user,
                email=data.get('email'),
                phone=data.get('phone', None),
                total=total,
                theater_name=theater['name'],
                theater_address=theater['address'],
                theater_id = theater_obj.id,
                screen_id = screen.id,
                screen_name=screen_name,
                show_date=f"{selected_date['year']}-{month_converter(selected_date['month'])}-{selected_date['day']}",
                show_time=selected_time,
                movie_title=selected_movie['title'],
                movie_poster=selected_movie['poster_path'],
                movie_backdrop=selected_movie['backdrop_path'],
                genres=", ".join(i['name'] for i in selected_movie["genres"]),
                is_snacks=bool(added_snacks),
            )

            for seat in selected_seats:
                BookedTicket.objects.create(
                    booking = booking,
                    seat_identifier=seat['seat']['identifier'],
                    seat_id=seat['seat']['id'],
                    price=seat['seat']['tier_price'],
                    tier_name = seat['seat']['tier_name'],
                )

            for snack in added_snacks:
                OrderSnack.objects.create(
                    booking=booking,
                    item_name=snack['name'],
                    description=snack['description'],
                    quantity=data['quantities'][str(snack['id'])],
                    image_url=snack['image_url'],
                    price=snack['price'],
                    is_vegetarian=snack['is_vegetarian'],
                    snack_id = snack['id']
                )

            line_items = []

            for seat in selected_seats:
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': f"Movie Ticket - {seat['seat']['tier_name']} (Seat: {seat['seat']['identifier']})",
                            'description': f"Show: {selected_movie['title']} | Theater: {theater['name']} | Screen: {screen_name} | Date: {selected_date['day']}-{selected_date['month']}-{selected_date['year']} | Time: {selected_time}",
                        },
                        'unit_amount': int(seat['seat']['tier_price'].split(".")[0]) * 100,
                    },
                    'quantity': 1,
                })

            for snack in added_snacks:
                print("snack: ",snack)
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': snack['name'],
                            'images': [snack['image_url']],
                        },
                        'unit_amount': int(snack['price'].split(".")[0]) * 100,
                    },
                    'quantity': data['quantities'][str(snack['id'])],
                })

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=line_items,
                success_url=f"{settings.BASE_API_URL}/booking/payment-success/{booking.id}",
                cancel_url=f"{settings.BASE_API_URL}/booking/payment-cancel/{booking.id}",


)
            booking.stripe_checkout_session_id = checkout_session.id
            booking.save()

            return Response({'id': checkout_session.id}, status=status.HTTP_200_OK)

    except Exception as e:
        print("e: ",e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class PaymentSuccessClass(APIView):
    permission_classes = []
    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            if booking.payment_status == 'success':
                return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-success?id={booking.id}")
        
            if not booking.stripe_checkout_session_id:
                return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-error?message=Checkout Session ID missing")
            
            session = stripe.checkout.Session.retrieve(booking.stripe_checkout_session_id)

            if session['payment_status'] == 'paid':
                booking.payment_status = 'success'
                booking.save()

            seats = BookedTicket.objects.filter(booking=booking)
            for seat in seats:
                seat_obj = SeatBooking.objects.get(id=seat.seat_id)
                seat_obj.status = "booked"
                seat_obj.user = booking.user
                seat_obj.visitor = booking.email
                seat_obj.save()

            snacks = OrderSnack.objects.filter(booking=booking)
            for snack in snacks:
                try:
                    theater_snack = TheaterSnack.objects.get(id=snack.snack_id)
                    if theater_snack.stock >= snack.quantity:
                        theater_snack.stock -= snack.quantity
                        theater_snack.save()
                    else:
                        return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-error?message=Insufficient+stock+for+snack+{snack.item_name}")

                except TheaterSnack.DoesNotExist:
                    return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-error?message=Snack+{snack.item_name}+not+found")


            return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-success?id={booking.id}")
        
        except Booking.DoesNotExist:
            return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/booking-error?message=Booking+not+found")
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        



class PaymentCancelClass(APIView):
    permission_classes = [AllowAny]

    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            
            if booking.payment_status == 'cancelled':
                return HttpResponseRedirect(
                    f"{settings.BASE_APP_URL}/user/payment-failed?message=Payment already cancelled"
                )

            booking.payment_status = 'cancelled'
            booking.save()

            seats = BookedTicket.objects.filter(booking=booking)
            for seat in seats:
                seat_obj = SeatBooking.objects.get(id=seat.seat_id)
                seat_obj.status = "available"
                seat_obj.save()

            return HttpResponseRedirect(
                f"{settings.BASE_APP_URL}/user/payment-failed?message=Booking Payment Cancelled"
            )

        except Booking.DoesNotExist:
            return HttpResponseRedirect(
                f"{settings.BASE_APP_URL}/user/payment-failed?message=Booking not found"
            )
        except Exception as e:
            return HttpResponseRedirect(
                f"{settings.BASE_APP_URL}/user/payment-failed?message=An error occurred: {str(e)}"
            )

        

class TicketDetailsClass(APIView):
    permission_classes = []

    def get(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            tickets = BookedTicket.objects.filter(booking=booking)
            snacks = OrderSnack.objects.filter(booking=booking)

            ticket_details = {
                "movie": {
                    "title": booking.movie_title,
                    "poster_path": booking.movie_poster,
                    "genres": [{"name": genre.strip()} for genre in booking.genres.split(",")]
                },
                "selectedTimeOg": booking.show_time,
                "selectedDate": 0,
                "dates": {
                    0: {
                        "day": booking.show_date.day,
                        "month": booking.show_date.month,
                        "dayOfWeek": calendar.day_name[booking.show_date.weekday()],
                        "year": booking.show_date.year,
                    }
                },
                "selectedTheater": {"name": booking.theater_name},
                "selectedScreen": booking.screen_name,
                "selectedSeats": [
                    {"seat": {"identifier": ticket.seat_identifier}}
                    for ticket in tickets
                ],
                "total": booking.total,
                "ticketTotal": sum(int(ticket.price) for ticket in tickets),
                "snackTotal": sum(int(snack.price[:-3]) * int(snack.quantity) for snack in snacks),
                "snacks": [
                    {
                        "id": snack.snack_id,
                        "name": snack.item_name,
                    }
                    for snack in snacks
                ],
                "QrCodeUrl": booking.qr_code,
                "BookingId": booking.booking_id,
            }

            return Response(ticket_details, status=status.HTTP_200_OK)

        except Booking.DoesNotExist:
            return Response({"message": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Exception as :", str(e))
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class BookedTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,ticket_mode):

        booking = Booking.objects.filter(payment_status = 'success', user = request.user)

        current_utc_time = datetime.now(datetime_timezone.utc)

        # Convert UTC to IST
        IST_OFFSET = timedelta(hours=5, minutes=30)
        current_ist_time = (current_utc_time + IST_OFFSET).time()



        match ticket_mode:
            case "pending":
                print("pending")
                q1 = Q(show_date__gt = datetime.now().date())
                q2 = Q(show_date = datetime.now().date()) and Q(show_time__gte = current_ist_time)
                booking = Booking.objects.filter(q1 or q2, payment_status = 'success', user = request.user, is_cancelled = False)
                print(booking)
            case "cancelled":
                print("cancelled")
                booking = Booking.objects.filter(is_cancelled = True, user = request.user)
                print(booking)
            case "watched":
                print("watched")
                booking = Booking.objects.filter(show_date__lte = datetime.now().date(), show_time__lte = current_ist_time, payment_status = 'success', user = request.user, is_cancelled = False)
                print(booking)

        serializer = BookingSerializer(booking, many=True)

        if serializer:
            return Response(data=serializer.data,status=status.HTTP_200_OK) 
        else:
            print(serializer.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        


class CancelTicketView(APIView):
    permission_classes = [IsAuthenticated]


    from decimal import Decimal

    def post(self, request):
        data = request.data
        current_utc_time = datetime.now(datetime_timezone.utc)

        IST_OFFSET = timedelta(hours=5, minutes=30)
        current_ist_time = current_utc_time + IST_OFFSET

        cancellation_cutoff_time = current_ist_time + timedelta(hours=4)

        try:
            booking = Booking.objects.get(id=data['ticket']['id'])
        except Booking.DoesNotExist:
            return Response({'message': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.is_cancelled:
            return Response({'message': 'Booking is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.show_date > current_ist_time.date() or (
            booking.show_date == current_ist_time.date() and booking.show_time > cancellation_cutoff_time.time()
        ):
            booking.is_cancelled = True

            qr_data = {'ticket_status': 'cancelled'}
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
            response = cloudinary.uploader.upload(buffer, folder="cancelled_qr_codes", public_id=booking.booking_id)
            booking.qr_code = response.get("secure_url")
            buffer.close()

            try:
                snacks = OrderSnack.objects.filter(booking=booking)
                for snack in snacks:
                    snack_og = TheaterSnack.objects.get(id=snack.snack_id)
                    snack_og.stock += snack.quantity
                    snack_og.save()
            except OrderSnack.DoesNotExist:
                pass

            tickets = BookedTicket.objects.filter(booking=booking)
            for ticket in tickets:
                seat = SeatBooking.objects.get(id=ticket.seat_id)
                seat.user = None
                seat.status = 'available'
                seat.reserved_at = None
                seat.save()

            if booking.stripe_checkout_session_id:
                try:
                    checkout_session = stripe.checkout.Session.retrieve(booking.stripe_checkout_session_id)
                    payment_intent_id = checkout_session.payment_intent

                    # Corrected the multiplication issue
                    total_amount = booking.total * Decimal('100')
                    refund_amount = int(total_amount * Decimal('0.75'))

                    stripe.Refund.create(
                        payment_intent=payment_intent_id,
                        amount=refund_amount,
                        reason='requested_by_customer'
                    )
                except stripe.error.StripeError as e:
                    return Response({'message': f'Refund failed: {e.user_message}'}, status=status.HTTP_400_BAD_REQUEST)

            booking.save()

            return Response({'message': 'Booking cancelled successfully.'}, status=status.HTTP_200_OK)

        else:
            return Response({'message': 'Cancellation is only available at least 4 hours before the showtime.'}, 
                            status=status.HTTP_400_BAD_REQUEST)


            

    def get(self,request):
        print("get in success")
        return Response(status=status.HTTP_200_OK)
    

class CancelTicketUnknownView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("here ", request.data)
        booking_id = request.data.get('booking_id')
        booking_user_id = request.data.get('id')
        user = request.data.get('user')

        current_utc_time = datetime.now(datetime_timezone.utc)
        IST_OFFSET = timedelta(hours=5, minutes=30)
        current_ist_time = current_utc_time + IST_OFFSET

        cancellation_cutoff_time = current_ist_time + timedelta(hours=4)

        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response({'message': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.is_cancelled:
            return Response({'message': 'Booking is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.show_date > current_ist_time.date() or (
            booking.show_date == current_ist_time.date() and booking.show_time > cancellation_cutoff_time.time()
        ):
            booking.is_cancelled = True

            qr_data = {'ticket_status': 'cancelled'}
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            snacks = OrderSnack.objects.filter(booking=booking)
            for snack in snacks:
                snack_og = TheaterSnack.objects.filter(id=snack.snack_id).first()
                if snack_og:
                    snack_og.stock += snack.quantity
                    snack_og.save()

            tickets = BookedTicket.objects.filter(booking=booking)
            for ticket in tickets:
                seat = SeatBooking.objects.filter(id=ticket.seat_id).first()
                if seat:
                    seat.user = None
                    seat.status = 'available'
                    seat.reserved_at = None
                    seat.save()


            if booking.stripe_checkout_session_id:
                try:
                    checkout_session = stripe.checkout.Session.retrieve(booking.stripe_checkout_session_id)
                    payment_intent_id = checkout_session.payment_intent
                    
                    total_amount = booking.total * 100
                    refund_amount = int(float(total_amount) * 0.75)
                    
                    stripe.Refund.create(
                        payment_intent=payment_intent_id,
                        amount=refund_amount,
                        reason='requested_by_customer'
                    )
                except stripe.error.StripeError as e:
                    return Response({'message': f'Refund failed: {e.user_message}'}, status=status.HTTP_400_BAD_REQUEST)

            booking.save()
            return Response({'message': f'Booking with ID {booking_id} cancelled successfully.'}, 
                            status=status.HTTP_200_OK)

        return Response(
            {'message': 'Cancellation is only available at least 4 hours before the showtime.'},
            status=status.HTTP_400_BAD_REQUEST
        )

            

       

class OwnerBookTicketsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        selected_theater = request.data.get("selected_theater")
        selected_seats = request.data.get("selected_seats")
        selected_date = request.data.get("selected_date")
        selected_time = request.data.get("selected_time")
        screen_name = request.data.get("screen_name")
        theater = Theater.objects.get(id=selected_theater['id'])
            
        screen = Screen.objects.get(theater__id=theater.id, name__iexact=screen_name)

        input_date = str(selected_date['year']) + '-' + str(month_converter(selected_date['month'])) + '-' + str(selected_date['date'])
        
        daily_show = get_object_or_404(DailyShow, schedule__showtime__screen__name = screen_name, show_date=input_date, show_time = selected_time)
        identifiers = []
        for seat in selected_seats:
            identifiers.append(seat['identifier'])

        if daily_show:
            seats = SeatBooking.objects.filter(daily_show = daily_show, identifier__in = identifiers)

        with transaction.atomic():
            user = None
            screen_name = screen_name
            selected_seats = selected_seats
            added_snacks = None
            selected_movie = daily_show.schedule.movie.title
            total = sum(float(seat['seat']['tier_price']) for seat in selected_seats)


            booking = Booking.objects.create(
                user=user,
                email=None,
                phone=None,
                total=total,
                theater_name=selected_theater["name"],
                theater_address=selected_theater["location"],
                screen_name=screen_name,
                screen_id = screen.id,
                theater_id = theater.id,
                show_date=input_date,
                show_time=selected_time,
                movie_title=selected_movie,
                movie_poster=daily_show.schedule.movie.poster_path,
                movie_backdrop=daily_show.schedule.movie.backdrop_path,
                genres=", ".join(i.name for i in daily_show.schedule.movie.genres.all()),
                is_snacks=bool(added_snacks),
            )
            for seat in selected_seats:
                BookedTicket.objects.create(
                    booking = booking,
                    seat_identifier=seat['seat']['identifier'],
                    seat_id=seat['seat']['id'],
                    price=seat['seat']['tier_price'],
                    tier_name = seat['seat']['tier_name'],
                )

            seats = BookedTicket.objects.filter(booking=booking)
            for seat in seats:
                seat_obj = SeatBooking.objects.get(id=seat.seat_id)
                seat_obj.status = "booked"
                seat_obj.user = booking.user
                seat_obj.visitor = booking.email
                seat_obj.save()


        theater_id = selected_theater['id']
        screen_time = selected_time
        show_date = selected_date
        movie_id = daily_show.schedule.movie.id


        if isinstance(show_date, dict):
            show_date = f"{show_date['year']}-{month_converter(show_date['month'])}-{show_date['date']}"

        if not all([theater_id, screen_name, screen_time, show_date]):
            return Response(
                {"error": "Missing required fields: theater_id, screen_name, screen_time, date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            theater = Theater.objects.get(id=theater_id)
            
            screen = Screen.objects.get(theater=theater, name__iexact=screen_name)
            
            time = ShowTime.objects.get(screen=screen, start_time=screen_time)
            movie_schedule = MovieSchedule.objects.get(showtime=time, showtime__screen__theater__id = theater.id, showtime__screen = screen, start_date__lte=show_date, end_date__gte=show_date)

            daily_show = DailyShow.objects.get(schedule=movie_schedule, show_date =  show_date, show_time = screen_time)
            seats = SeatBooking.objects.filter(daily_show=daily_show).order_by('position', 'identifier')
            
            grouped_seats = defaultdict(list)
            for seat in seats:
                data = SeatLayoutSerializer(seat).data
                grouped_seats[seat.position].append(data)

        except Theater.DoesNotExist:
            return Response(
                {"error": f"Theater with id {theater_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Screen.DoesNotExist:
            return Response(
                {"error": f"Screen '{screen_name}' not found in theater with id {theater_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ShowTime.DoesNotExist:
            return Response(
                {"error": f"ShowTime with start time '{screen_time}' not found for screen '{screen_name}'."},
                status=status.HTTP_404_NOT_FOUND
            )
        except MovieSchedule.DoesNotExist:
            return Response(
                {"error": "Movie schedule not found for the specified showtime."},
                status=status.HTTP_404_NOT_FOUND
            )
        except DailyShow.DoesNotExist:
            return Response(
                {"error": f"No daily show found on date '{show_date}' for the specified schedule."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(data=grouped_seats, status=status.HTTP_200_OK)