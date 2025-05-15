from django.db import models
from accounts.models import User

class Genre(models.Model):
    tmdb_id             = models.IntegerField()
    name                = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Language(models.Model):
    name                = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Person(models.Model):
    name                = models.CharField(max_length=255)
    image               = models.URLField(max_length=200, blank=True, null=True) 
    def __str__(self):
        return self.name


class Movie(models.Model):
    title               = models.CharField(max_length=255)
    tmdb_id             = models.IntegerField(blank=True, null=True)
    release_date        = models.DateField(blank=True, null=True)
    vote_average        = models.FloatField(blank=True, default=0)
    runtime             = models.IntegerField(blank=True, null=True)
    description         = models.TextField(blank=True, default="No description available.")
    poster_path         = models.URLField(max_length=500, blank=True, null=True)  
    backdrop_path       = models.URLField(max_length=500, blank=True, null=True)  
    video_key           = models.CharField(max_length=225, blank=True, null=True)
    is_listed           = models.BooleanField(default=True)
    
    genres              = models.ManyToManyField(Genre, related_name='movies') 
    languages           = models.ManyToManyField(Language, related_name='movies')  

    def __str__(self):
        return self.title
    

    def recalculate_vote_average(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
            self.vote_average = round(avg_rating, 1)
            self.save()
        else:
            self.vote_average = 0
            self.save()
    


class MovieRole(models.Model):
    person              = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='roles') 
    movie               = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='roles')  
    role                = models.CharField(max_length=50, blank=True, null=True)
    character_name      = models.CharField(max_length=255, blank=True, null=True)
    is_cast             = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.person.name} - {self.role} in {self.movie.title}"

class Hashtag(models.Model):
    heading = models.CharField(max_length=100, unique=False)
    rated_at = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.heading


class Review(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    hashtags = models.ManyToManyField(Hashtag, related_name='reviews')
    content = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f'Review by {self.user.email} for {self.movie.title}'


class ReviewReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_reactions')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=7, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.email} {self.reaction}d review {self.review.id}"
