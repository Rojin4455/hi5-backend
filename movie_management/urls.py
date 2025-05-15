from django.urls import path
from .views import *

urlpatterns = [
    path('add-movie/', AddMovieView.as_view(), name='add-movie'),
    path('remove-movie/', RemoveMovieView.as_view(), name='add-movie'),
    
    # path('check-movie/<id:int>/', CheckMovieView.as_view(), name='check-movie'),
    path('get-movie/', GetMovieView.as_view(), name='get-movie'),
    # path('full-movie-details/<id:movieId>/')
    path('location-movies/', LocationMoviesView.as_view(), name='location-movies'),
    path('location-theaters/', LocationTheatersView.as_view(), name='location-theaters'),
    path('movie-hashtags/', MovieHashtagsView.as_view()),
    path('add-review/', MovieReviewView.as_view()),
    path('get-reviews/<int:movieId>/', MovieReviewView.as_view()),
    path('add-review-reaction/', ReviewReactionView.as_view()),
    path('inactive-movie/',InactiveMovieView.as_view()),
    path('activate-movie/',ActiveMovieView.as_view()),
    path('get-movie-ids/', GetMovieIDsView.as_view()),
]
