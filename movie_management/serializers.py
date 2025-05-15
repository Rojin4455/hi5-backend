from rest_framework import serializers
from .models import Genre, Language, Person, Movie, MovieRole, Hashtag, Review, ReviewReaction
from screen_management.models import MovieSchedule,ShowTime, DailyShow
from theater_managemant.models import Theater,Screen

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['tmdb_id', 'name']

    def to_internal_value(self, data):
        
        try:
            genre = Genre.objects.get(tmdb_id=data.get('tmdb_id'))
        except Genre.DoesNotExist:
            genre = None

        if genre is not None:
            return genre
        
        
        return super().to_internal_value(data)



        return genre

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name']

    def to_internal_value(self, data):
        
        try:
            language = Language.objects.get(name=data.get('name'))
        except Language.DoesNotExist:
            language = None

        if language is not None:
            return language
        return super().to_internal_value(data)

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['name', 'image']

class MovieRoleSerializer(serializers.ModelSerializer):
    person = PersonSerializer()

    class Meta:
        model = MovieRole
        fields = ['person', 'role', 'character_name', 'is_cast']

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    languages = LanguageSerializer(many=True)
    roles = MovieRoleSerializer(many=True)

    class Meta:
        model = Movie
        fields = [
            'title', 'tmdb_id', 'release_date', 'vote_average', 'runtime', 
            'description', 'poster_path', 'backdrop_path', 'video_key', 
            'is_listed', 'genres', 'languages', 'roles','id',   
        ]

    def create(self, validated_data):
        genres_data = validated_data.pop('genres')
        languages_data = validated_data.pop('languages')
        roles_data = validated_data.pop('roles')
        movie = Movie.objects.create(**validated_data)

        for genre_data in genres_data:
            if isinstance(genre_data, Genre):
                genre = genre_data
            else:
                genre, created = Genre.objects.get_or_create(**genre_data)
            movie.genres.add(genre)

        for language_data in languages_data:
            if isinstance(language_data, Language):
                language = language_data
            else:
                language, created = Language.objects.get_or_create(**language_data)
            movie.languages.add(language)

        for role_data in roles_data:
            person_data = role_data.pop('person')
            person, created = Person.objects.get_or_create(**person_data)
            movie_role_obj = MovieRole.objects.create(person=person, movie=movie, **role_data)
            movie_role_obj.is_cast = True if role_data['character_name'] else False
            movie_role_obj.save()
            


        return movie
    




class MovieScheduleSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()
    class Meta:
        model = MovieSchedule
        fields = '__all__'


class HashTagSerializers(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    selectedHashtags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )
    movieId = serializers.IntegerField(write_only=True)
    content = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Review
        fields = ['rating', 'content', 'selectedHashtags', 'movieId']

    def create(self, validated_data):
        rating = validated_data['rating']
        movie_id = validated_data['movieId']
        content = validated_data.get('content', '')
        selected_hashtags = validated_data.get('selectedHashtags', [])

        movie = Movie.objects.get(id=movie_id)

        user = self.context['request'].user
        review = Review.objects.create(
            user=user,
            movie=movie,
            content=content,
            rating=rating
        )
        score = 0
        if rating <=3:
            score = 3
        elif rating <= 6:
            score = 6
        else:
            score = 10
        print("full rext: ", selected_hashtags)
        for hashtag_text in selected_hashtags:
            print("hashtags: ",hashtag_text)
            hashtag, created = Hashtag.objects.get_or_create(heading=hashtag_text, rated_at = score)
            print("hashtags: ",hashtag_text)

            review.hashtags.add(hashtag)



        return review


class ReviewReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReaction
        fields = '__all__'


class AllReviewSerializer(serializers.ModelSerializer):
    hashtags = HashTagSerializers(many=True)
    user = serializers.SerializerMethodField()
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    review_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'movie_title', 'content', 'rating', 'hashtags',
            'created_at', 'updated_at', 'likes_count', 'dislikes_count', 'review_reaction'
        ]

    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
            }
        return None
    
    def get_review_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            if reaction:
                return ReviewReactionSerializer(reaction).data
        return None






# class ShowTimeSerializer(serializers.ModelSerializer):
#     show_time = serializers.TimeField(source='start_time')

#     class Meta:
#         model = ShowTime
#         fields = ['show_time']

# class ScreenSerializer(serializers.ModelSerializer):
#     showtimes = ShowTimeSerializer(many=True, read_only=True)

#     class Meta:
#         model = Screen
#         fields = ['name', 'type', 'capacity', 'showtimes']

# class TheaterSerializer(serializers.ModelSerializer):
#     screens = ScreenSerializer(many=True, read_only=True)

#     class Meta:
#         model = Theater
#         fields = ['name', 'location', 'lat', 'lng', 'screens']

# class TheaterMovieScheduleSerializer(serializers.ModelSerializer):
#     theater = serializers.SerializerMethodField()

#     def get_theater(self, obj):
#         print("obj:",obj)

#         nearby_theaters = Theater.objects.filter(screens__showtimes__schedules=obj)
#         return TheaterSerializer(nearby_theaters, many=True).data

#     class Meta:
#         model = MovieSchedule
#         fields = ['theater', 'start_date', 'end_date']




from rest_framework import serializers


class DailyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyShow
        fields = ['show_date', 'show_time']

class ShowTimeSerializer(serializers.ModelSerializer):
    daily_shows = DailyShowSerializer(many=True, read_only=True)

    class Meta:
        model = ShowTime
        fields = ['id', 'start_time', 'daily_shows']

class ScreenSerializer(serializers.ModelSerializer):
    showtimes = ShowTimeSerializer(many=True, read_only=True)

    class Meta:
        model = Screen
        fields = ['id', 'name', 'type', 'capacity', 'showtimes']

class TheaterSerializer(serializers.ModelSerializer):
    screens = ScreenSerializer(many=True, read_only=True)

    class Meta:
        model = Theater
        fields = ['id', 'name', 'location', 'screens']



        
