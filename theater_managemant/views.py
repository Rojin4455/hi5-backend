from collections import defaultdict
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
import rest_framework.status
from rest_framework.permissions import IsAuthenticated
from .serializers import TheaterSerializer,ScreenSerializer,SnackCategorySerializer, SnackItemSerializer, TheaterSnackSerializer, TheaterFullSnacksSerializer
from rest_framework import status
from .models import Theater,Screen,Tier,Seat,ScreenImage,SnackCategory,SnackItem,TheaterSnack
import json
import cloudinary.uploader
from django.db.models import Prefetch
from accounts.models import User
from booking_management.models import Booking,BookedTicket
from .serializers import BookingSerializer
from django.db.models import Sum, F, Count
from datetime import timedelta, date
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from movie_management.models import Movie









class AddTheaterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data = request.data.copy()
        data['owner'] = request.user.id


        image_file = request.FILES.get('photo')
        if image_file:
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="theater_photos"
            )
            image_url = upload_result.get('secure_url')
            data['image_url'] = image_url


        serializer = TheaterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTheaterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        theater = Theater.objects.filter(owner=request.user)
        serializer = TheaterSerializer(theater,many=True)

        return Response(serializer.data)
    

class GetTheaterDetailsClass(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,theaterId):

        try:
            theater = Theater.objects.get(id = theaterId)
            screens= Screen.objects.filter(theater = theater)

            # screen_details = {}
            # tier_details = {}

            # for screen in screens:
            #      image = ScreenImage.objects.filter(screen=screen)
            #      tier = Tier.objects.filter(screen=screen)
            #      for i in tier:
            #         try:
            #             seats = Seat.objects.get(tier=i)
            #             tier_details[i.name] = seats
            #         except:
            #              tier_details[i.name] = None
            #      screen_details[screen.name] = {"images":image,"tier":tier_details}

            # print(f"screen: {screen_details}")
            theater_serializer = TheaterSerializer(theater, many=False)
            screen_serializer = ScreenSerializer(screens, many=True)

            return Response({"message":"theater details","data":theater_serializer.data,"screen_datas":screen_serializer.data},status=status.HTTP_200_OK)
        except Theater.DoesNotExist:
            return Response({"message":"theater is not found in that id {theaterId}"},status=status.HTTP_404_NOT_FOUND)
        

class AddScreenClass(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,theaterId):
        try:
                theater = Theater.objects.get(id=theaterId)
        except Theater.DoesNotExist:
                return Response({"error": "Theater not found"}, status=status.HTTP_404_NOT_FOUND)
            
        tiers_data = json.loads(request.POST.get('tiers', '[]'))
        data = request.data.dict()
        # data = request.data.copy()
        # data.setlist('tiers', tiers_data)
        data['theater'] = theater.id

        if 'tiers' in data:
                try:
                    data['tiers'] = json.loads(data['tiers'])
       

                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format for tiers"}, status=status.HTTP_400_BAD_REQUEST)
        print("request data after parsing before sending to serializer: ",data)
        serializer = ScreenSerializer(data=data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("serialiser data: ",serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ScreenDetailsClass(APIView):
     permission_classes = [IsAuthenticated]

     def get(self,request,screen_id):
        try:

            print("after here reached",screen_id)
            screen = Screen.objects.get(id = screen_id)
            screen = Screen.objects.prefetch_related(
            Prefetch('tiers', queryset=Tier.objects.order_by('id'))).get(id=screen_id)
            theater_id = screen.theater.id
            serializer = ScreenSerializer(screen,many=False)
            print("reached", screen)
            return Response({"message":"screen details found successfully","data":serializer.data,"theater_id":theater_id}, status=status.HTTP_200_OK)
        except Exception as e:
             print(str(e))
             return Response({"message":"Screen not exist in this id"}, status=status.HTTP_404_NOT_FOUND)
        



class SnackCategoryClass(APIView):
    permission_classes = [IsAuthenticated]


    def post(self,request):
        category_name = request.data.get('category_name')
        try:
            owner = User.objects.get(id=request.user.id)
            try:
                SnackCategory.objects.get(name=category_name, owner=owner)
                return Response({"message":"Category is Already exists"}, status=status.HTTP_400_BAD_REQUEST)
            except SnackCategory.DoesNotExist:
                new_category = SnackCategory.objects.create(name=category_name, owner=owner)
                serializer = SnackCategorySerializer(new_category)
                print("serializers", serializer.data)
                return Response({"message":"category created successfully","data":serializer.data}, status=status.HTTP_201_CREATED)
                    
            
                    
        except User.DoesNotExist:
            return Response({"message":"Owner is not Found"}, status=status.HTTP_404_NOT_FOUND)
        
    def get(self, request):
        all_categories = SnackCategory.objects.all()
        
        serializer = SnackCategorySerializer(all_categories, many=True)
        return Response({"message":"All categories fetched successfully", "data":serializer.data}, status=status.HTTP_200_OK)
    


class OwnerSnacksClass(APIView):
    def post(self, request):
        snack_data = request.data
        print("snack data: ", snack_data)

        try:
            category = SnackCategory.objects.get(name=snack_data['category'], owner=request.user)
        except SnackCategory.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        snack_data = snack_data.copy()
        snack_data['category'] = category.id
        snack_data['is_vegetarian'] = False if snack_data.pop('is_vegetarian') == ["false"] else True

        serializer = SnackItemSerializer(data=snack_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        


class TheaterSnacksClass(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        print("request data:",request.data)
        serializer = TheaterSnackSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self,request,theater_id):
        print("theater id: ",theater_id)
        theater = Theater.objects.get(id=theater_id)
        existing_snacks = TheaterSnack.objects.filter(theater=theater)
        available_snacks = SnackItem.objects.exclude(theater_snack_items__in=existing_snacks)
        available_categories = SnackCategory.objects.filter(snack_items__in=available_snacks).distinct()
        serializer = SnackCategorySerializer(available_categories, many=True, context={'snacks': available_snacks})

        return Response({"message":"All categories fetched successfully in theater snacks", "data":serializer.data}, status=status.HTTP_200_OK)
    
class AddedSnacksClass(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,theater_id):
        theater = Theater.objects.get(id=theater_id)
        existing_snacks = TheaterSnack.objects.filter(theater=theater)
        serializer = TheaterFullSnacksSerializer(existing_snacks, many=True)
        # added_snacks = SnackItem.objects.filter(theater_snack_items__in=existing_snacks)
        # available_categories = SnackCategory.objects.filter(snack_items__in=added_snacks).distinct()
        # serializer = SnackCategorySerializer(available_categories, many=True, context={'snacks': added_snacks})

        return Response({"message":"All categories fetched successfully in theater added snacks", "data":serializer.data}, status=status.HTTP_200_OK)
    

class UpdateSnackTheater(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        snack_id = request.data.get('snack_id')
        new_stock = request.data.get('stock')
        price = request.data.get('price')

        try:
            snack = TheaterSnack.objects.get(id=snack_id)
            snack.stock = new_stock if new_stock else snack.stock
            snack.price = price if price else snack.price
            snack.save()
            return Response(status=status.HTTP_200_OK)

        except TheaterSnack.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


    def delete(self,request,snack_id):
        if snack_id:
            try:
                snack = TheaterSnack.objects.get(id=snack_id)
                snack.delete()
                print("snack is deleted")
                return Response(status=status.HTTP_200_OK)
            except TheaterSnack.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({'message':"invalid details provided"}, status=status.HTTP_400_BAD_REQUEST)






class DashBoardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        owner = request.user
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, status=400)

        theaters = Theater.objects.filter(owner=owner)

        if not theaters.exists():
            return Response({'error': 'No theaters found for this owner'}, status=404)

        bookings = Booking.objects.filter(
            theater_id__in=theaters.values_list('id', flat=True),
            show_date__range=[start_date, end_date],
            is_cancelled = False
        ).values(
            'theater_name', 'screen_name'
        ).annotate(
            total_bookings=Count('book_ticket__id')
        )

        grouped_data = defaultdict(list)

        for booking in bookings:
            grouped_data[booking['theater_name']].append({
                "screen_name": booking['screen_name'],
                "total_bookings": booking['total_bookings']
            })

        result = [
            {
                "theater_name": theater_name,
                "screens": screens
            }
            for theater_name, screens in grouped_data.items()
        ]

        bookings = Booking.objects.filter(theater_id__in=theaters, is_cancelled = False)
        total_bookings = 0
        total_revenue = 0
        movie_titles = []
        total_theaters = Theater.objects.filter(owner=owner).count()
        movie_dict = dict()
        for booking in bookings:
            count = BookedTicket.objects.filter(booking=booking).count()
            total_bookings += count
            total_revenue += booking.total
            movie_titles.append(booking.movie_title)
            if booking.movie_title in movie_dict:
                movie_dict[booking.movie_title][0] += count
            else:
                movie_dict[booking.movie_title] = [count,{"poster_path":booking.movie_poster,"genres":booking.genres}]
            
        # top_movies = Movie.objects.filter(title__in=movie_titles)
        # print(top_movies)

        sorted_movie_dict = sorted(movie_dict.items(), key=lambda x: x[1][0], reverse=True)
        # sorted_movie_dict = dict(sorted_movie_dict)

        title_data = {
            "total_bookings":total_bookings,
            "total_revenue":total_revenue,
            "total_theaters":total_theaters,
            "top_movies":sorted_movie_dict,
        
        }

        
        # serializer = BookingSerializer(bookings, many=True)
        return Response({'success': result, "title_data":title_data})


class BookingTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        owner = request.user
        theaters = Theater.objects.filter(owner=owner)

        if not theaters.exists():
            return Response({'error': 'No theaters found for this owner'}, status=404)

        theater_ids = theaters.values_list('id', flat=True)
        time_period = request.query_params.get('time_period', 'daily')
        today = date.today()

        # Default date range based on `time_period`
        if time_period == 'daily':
            start_date = today - timedelta(days=7)
            date_trunc = TruncDay
            interval = 'day'
        elif time_period == 'weekly':
            start_date = today - timedelta(weeks=5)
            date_trunc = TruncWeek
            interval = 'week'
        elif time_period == 'monthly':
            start_date = today.replace(day=1) - timedelta(days=120)
            date_trunc = TruncMonth
            interval = 'month'
        elif time_period == 'max':
            start_date = date(2024,1,1)
            date_trunc = TruncMonth
            interval = 'month'
        else:
            return Response({'error': 'Invalid time period'}, status=400)

        # Query bookings and group by date intervals
        bookings = BookedTicket.objects.filter(
            booking__theater_id__in=theater_ids,
            booking__is_cancelled = False,
        )
        if start_date:
            bookings = bookings.filter(booking__show_date__range=[start_date, today])

        bookings = bookings.annotate(interval=date_trunc('booking__show_date')).values('interval').annotate(total=Count('id'))

        # Create a default response structure with all intervals
        if start_date:
            labels = []
            current = start_date
            while current <= today:
                if interval == 'day':
                    labels.append(current)
                    current += timedelta(days=1)
                elif interval == 'week':
                    labels.append(current)
                    current += timedelta(weeks=1)
                elif interval == 'month':
                    labels.append(current.replace(day=1))
                    current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            labels = sorted({b['interval'] for b in bookings})

        formatted_labels = [label.strftime('%Y-%m-%d') if interval == 'day'
                            else label.strftime('%Y-%W') if interval == 'week'
                            else label.strftime('%Y-%m') for label in labels]

        # Fill missing intervals with total = 0
        data_dict = {b['interval']: b['total'] for b in bookings}

        data = [{"label": formatted_label, "total": data_dict.get(label, 0)} 
                for label, formatted_label in zip(labels, formatted_labels)]

        return Response(data)



class BookingReportView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        owner = request.user
        try:
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')

            theaters = Theater.objects.filter(owner = owner).values_list('id')

            if not start_date or not end_date:
                return Response({"error": "Invalid date range"}, status=status.HTTP_400_BAD_REQUEST)

            bookings = Booking.objects.filter(show_date__range=[start_date, end_date], theater_id__in = theaters)

            total_income = BookedTicket.objects.filter(
                booking__show_date__range=[start_date, end_date]
            ).aggregate(total_income=Sum('price'))['total_income'] or 0

            booking_details = []
            for booking in bookings:
                tickets = BookedTicket.objects.filter(booking=booking).values(
                    'seat_identifier', 'seat_id', 'price', 'tier_name'
                )
                booking_details.append({
                    "booking_id": booking.booking_id,
                    "movie_title": booking.movie_title,
                    "show_date": booking.show_date,
                    "show_time": booking.show_time,
                    "theater_name": booking.theater_name,
                    "screen_name": booking.screen_name,
                    "total": booking.total,
                    "tickets": list(tickets),
                })

            response_data = {
                "bookings": booking_details,
                "total_income": total_income,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        


