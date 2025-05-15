from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review

@receiver(post_save, sender=Review)
def update_movie_vote_average_on_save(sender, instance, **kwargs):
    print("on save")

    instance.movie.recalculate_vote_average()

@receiver(post_delete, sender=Review)
def update_movie_vote_average_on_delete(sender, instance, **kwargs):
    instance.movie.recalculate_vote_average()