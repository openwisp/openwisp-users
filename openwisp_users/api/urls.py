from django.conf.urls import url
from openwisp_users import settings as app_settings

from . import views

urlpatterns = []

app_name = 'users'

if app_settings.USERS_AUTH_API:
    urlpatterns += [
        url(r'^user/token/', views.obtain_auth_token, name='user_auth_token')
    ]
