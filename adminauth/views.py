from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import AdminLoginSerializer,TheaterSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from accounts.models import User
from django.db.models import F, Value
from django.db.models.functions import Coalesce,Concat
from ownerauth.serializers import TheaterOwnerSerializer
from theater_managemant.models import Theater
from django.shortcuts import get_object_or_404
from booking_management.models import BookedTicket, Booking
from django.db.models import Sum, F, Count
from collections import defaultdict
from datetime import timedelta, date
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth



class AdminLogin(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = AdminLoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            print("before authenticate")
            user = authenticate(request,email=email, password=password)
            print("after authenticate",user)
            if user is not None:
                if user.is_staff:
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'email':user.email,
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'is_admin':user.is_superuser
                    },status=status.HTTP_200_OK)


                else:
                    return Response({"error": "User is not an admin."}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # If the serializer is not valid, return errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     




class AllUsers(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data = request.data
        page_no = data.get('currentPage')
        users_per_page = data.get('usersPerPage')
      
        users = User.objects.filter(is_staff=False, is_owner=False).select_related('user_profile').annotate(
            image_url=Coalesce(F('user_profile__image_url'), Value(None))
        ).values('id','email', 'date_joined', 'phone', 'is_active', 'image_url').order_by("email")[users_per_page*(page_no-1):users_per_page+users_per_page*(page_no-1)]
        totalcount = User.objects.count()
        return Response({"message":"users frtched successfully","allUsers":users,'totalCount':totalcount},status=status.HTTP_200_OK)
        # BASE_URL = "http://127.0.0.1:8000/"
        # users = User.objects.filter(is_staff=False).select_related('user_profile').annotate(
        #     profile_pic=Coalesce(
        #         Concat(Value(BASE_URL), F('user_profile__profile_pic')),
        #         Value(f'{BASE_URL}default-profile-pic.jpg')  # Fallback to a default image if profile_pic is None
        #     )
        # ).values('email', 'date_joined', 'phone', 'is_active', 'profile_pic')

        # return Response({"message":"users frtched successfully","allUsers":users},status=status.HTTP_200_OK)

        pass

class ChangeStatus(APIView):
    permission_classes = [IsAuthenticated]

    def put(self,request,user_id):

        print("user id:", user_id)
        
        # Fetch the user object by user_id
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        
        # Toggle the user's is_active status
        user.is_active = not user.is_active
        user.save()  # Save the updated user status
        
        print("User status updated")
        
        return Response({"message": "User status updated successfully"})


class GetTheaterOwnersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        owners = User.objects.filter(is_owner=True)
        print(owners)
        serializer = TheaterOwnerSerializer(owners, many=True)  # Serialize the data
        return Response({"message": "All owners retrieved", "allOwners": serializer.data}, status=status.HTTP_200_OK)


class GetRequestedOwnersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        owners = User.objects.filter(is_owner=True, is_approved=False)
        print(owners)
        serializer = TheaterOwnerSerializer(owners, many=True)  # Serialize the data
        return Response({"message": "All owners retrieved", "allOwners": serializer.data}, status=status.HTTP_200_OK)
    

class GetOwnerDetails(APIView):
    def get(self, request, ownerId):
        try:
            owner = User.objects.get(id=ownerId)
            serializer = TheaterOwnerSerializer(owner)
            print("owner got", owner)
            
            print("serializer obj", serializer)
            return Response({"message": "Owner found successfully", "owner_data": serializer.data}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            print("Owner not found with that ID")
            return Response({"message": "Owner not found"}, status=status.HTTP_404_NOT_FOUND)


    

class ApproveTheaterOwnerView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request, owner_id):
        try:
            owner = User.objects.get(id = owner_id)
            owner.is_approved = True
            owner.is_active = True
            owner.save()
            return Response({"message": "Theater owner approved successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Theater owner not found"}, status=status.HTTP_404_NOT_FOUND)



class DisapproveTheaterOwnerView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request, owner_id):
        try:
            owner = User.objects.get(id = owner_id)
            owner.is_approved = False
            owner.is_active = False
            owner.save()
            return Response({"message": "Theater owner Disapproved successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Theater owner not found"}, status=status.HTTP_404_NOT_FOUND)



class OwnerAllDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,id):
        try:
            # Fetch the owner by id
            owner = get_object_or_404(User, id=id)
            
            # Fetch all theaters owned by this owner
            theaters = Theater.objects.filter(owner=owner)

            # Serialize owner and theater data
            owner_data = {
                'id': owner.id,
                'first_name': owner.first_name,
                'last_name': owner.last_name,
                'email': owner.email,
                'phone': owner.phone,
                'theaters': TheaterSerializer(theaters, many=True).data  # serialize theaters
            }
            
            return Response({
                "message": "Owner details found successfully",
                "owner_data": owner_data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "Owner not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"message": "An error occurred: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class DisapproveTheaterclass(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,theaterId):
        try:
            theater = Theater.objects.get(id = theaterId)
            theater.is_approved = False
            theater.save()
            return Response({"message": "Theater Disapproved successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Theater not found"}, status=status.HTTP_404_NOT_FOUND)
        

class ApproveTheaterclass(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self,request,theaterId):
        print("TT")
        try:
            theater = Theater.objects.get(id = theaterId)
            theater.is_approved = True
            theater.save()
            return Response({"message": "Theater Approved successfully"}, status=status.HTTP_200_OK)
        except Theater.DoesNotExist:
            return Response({"error": "Theater not found"}, status=status.HTTP_404_NOT_FOUND)



class DashBoardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        admin = request.user
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, status=400)

        admin = User.objects.filter(id=admin.id)

        if not admin.exists():
            return Response({'error': 'No theaters found for this owner'}, status=404)

        bookings = Booking.objects.filter(
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

        bookings = Booking.objects.filter(is_cancelled = False)
        total_bookings = 0
        total_revenue = 0
        movie_titles = []
        total_theaters = Theater.objects.all().count()
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


        sorted_movie_dict = sorted(movie_dict.items(), key=lambda x: x[1][0], reverse=True)
        total_users = User.objects.filter(is_superuser=False,is_owner=False).count()

        title_data = {
            "total_bookings":total_bookings,
            "total_revenue":total_revenue,
            "total_theaters":total_theaters,
            "top_movies":sorted_movie_dict,
            "total_users":total_users,
        
        }

        
        return Response({'success': result, "title_data":title_data})
    

class BookingReportView(APIView):
    def post(self, request):
        try:
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')

            if not start_date or not end_date:
                return Response({"error": "Invalid date range"}, status=status.HTTP_400_BAD_REQUEST)

            bookings = Booking.objects.filter(show_date__range=[start_date, end_date])

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
        


class BookingTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):


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