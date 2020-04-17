from django.conf.urls import url
from openwisp_users import settings as app_settings

from . import views

urlpatterns = []

if app_settings.USERS_AUTH_API:
    urlpatterns += [
        url(r'^users/token/', views.obtain_auth_token, name='api-token-auth')
    ]
