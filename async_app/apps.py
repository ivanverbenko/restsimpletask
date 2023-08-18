from django.apps import AppConfig


class AsyncAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'async_app'
