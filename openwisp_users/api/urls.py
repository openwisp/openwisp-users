from django.conf.urls import url

from openwisp_users import settings as app_settings

from . import views


def get_api_urls(api_views=None):
    urlpatterns = []
    if api_views is None:
        api_views = views
    if app_settings.USERS_AUTH_API:
        urlpatterns += [
            url(r'^user/token/', views.obtain_auth_token, name='user_auth_token')
        ]
    return urlpatterns


urlpatterns = get_api_urls()
