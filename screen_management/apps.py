from django.apps import AppConfig


class ScreenManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'screen_management'

    def ready(self):
        import screen_management.signals