from django.apps import AppConfig


class MovieManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movie_management'


    def ready(self):
        import movie_management.signals