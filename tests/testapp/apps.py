from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = 'testapp'
    label = 'testapp'
    default_auto_field = 'django.db.models.AutoField'
