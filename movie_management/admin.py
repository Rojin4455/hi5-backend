from django.contrib import admin
from .models import Movie,Person,Genre,Language,MovieRole, Hashtag, Review, ReviewReaction

admin.site.register(Movie)
admin.site.register(Person)
admin.site.register(Genre)
admin.site.register(Language)
admin.site.register(MovieRole)

admin.site.register(Hashtag)
admin.site.register(Review)
admin.site.register(ReviewReaction)

