from rest_framework import serializers
from theater_managemant.models import Seat,Screen,Tier
from theater_managemant.serializers import TierSerializer
from screen_management.models import ShowTime,DailyShow,MovieSchedule
from movie_management.models import Movie
from datetime import timedelta
from datetime import datetime, time, timedelta
import pytz


class SeatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seat
        fields = ['row', 'column', 'is_available', 'identifier']




class SeatLayoutSerializer(serializers.Serializer):
    theaterId = serializers.IntegerField()
    grid_columns = serializers.IntegerField()
    grid_rows = serializers.IntegerField()
    seatLayout = SeatSerializer(many=True)
    tierFullDetails = TierSerializer()
    activeSeatCount = serializers.IntegerField()

    def create(self, validated_data):
        theater_id = validated_data.get('theaterId')
        seat_layout = validated_data.get('seatLayout')
        rows = validated_data.get('grid_rows')
        columns = validated_data.get('grid_columns')
        count = validated_data.get('activeSeatCount')

        try:
            tier_id = self.context.get('tier_id')


            tier = Tier.objects.get(id=tier_id)
        except Tier.DoesNotExist:
            raise serializers.ValidationError({"tierFullDetails": f"Tier with id {tier_id} does not exist"})

        tier.rows = rows
        tier.columns = columns
        tier.total_seats = count
        tier.save()

        prev_seats = Seat.objects.filter(tier=tier)
        new_seat_set = set((seat_data['row'], seat_data['column']) for seat_data in seat_layout if seat_data['is_available'])

        for prev_seat in prev_seats:
            if (prev_seat.row, prev_seat.column) not in new_seat_set:
                prev_seat.delete()


        for seat_data in seat_layout:
            if seat_data['is_available']:
                
                Seat.objects.update_or_create(
                    tier=tier,
                    row=seat_data['row'],
                    column=seat_data['column'],
                    is_available = True,
                    identifier = seat_data['identifier']
                )
        return validated_data
    



class ShowTimesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTime
        fields = "__all__"



class DailyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyShow
        fields = ['show_date', 'show_time']



class MovieScheduleSerializer(serializers.ModelSerializer):
    daily_shows = DailyShowSerializer(many=True, read_only=True)
    selected_times = serializers.ListField(
        child=serializers.TimeField(format='%H:%M'), write_only=True
    )
    movie_id = serializers.IntegerField(write_only=True)
    screen_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MovieSchedule
        fields = ['start_date', 'end_date', 'selected_times', 'movie_id', 'screen_id', 'daily_shows','id']

    def create(self, validated_data):
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        selected_times = validated_data.pop('selected_times')
        movie = Movie.objects.get(id=validated_data.pop('movie_id'))
        screen = Screen.objects.get(id=validated_data.pop('screen_id'))
        show_times = ShowTime.objects.filter(screen=screen)

        print("show time: ", show_times)
        print("selected time: ", selected_times)
        print("screen: ", screen)
        print("start_date: ", start_date)
        print("end_date: ", end_date)
        print("movie: ", movie)

        # Matching times will hold the ShowTime objects that match selected times
        matching_times = []
        
        for selected_time in selected_times:
            for show_time in show_times:
                if show_time.start_time == selected_time:  # Compare times directly
                    matching_times.append(show_time)

        print("Matching Times:", matching_times)

        # Create the MovieSchedule record for each matching showtime
        for time in matching_times:
            schedule, created = MovieSchedule.objects.get_or_create(
                showtime=time,
                movie=movie,
                start_date=start_date,
                end_date=end_date,
            )
            if created:
                print(f"Created schedule for {time} on {start_date} to {end_date}")

        # Uncomment this part if you want to generate DailyShow records
        # current_date = start_date
        # while current_date <= end_date:
        #     for time in matching_times:
        #         DailyShow.objects.create(
        #             schedule=schedule,
        #             show_date=current_date,
        #             show_time=time.start_time  # Save the TimeField value
        #         )
        #     current_date += timedelta(days=1)

        return schedule
    







class ShowTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTime
        fields = ['id', 'screen', 'start_time']