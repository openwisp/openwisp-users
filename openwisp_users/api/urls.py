from django.conf.urls import url
from django.urls import path

from openwisp_users import settings as app_settings

from . import views


def get_api_urls(api_views=None):
    urlpatterns = []
    if api_views is None:
        api_views = views
    urlpatterns += [
        path('users/organization/', views.organization_list, name='organization_list',),
        path(
            'users/organization/<str:pk>/',
            views.organization_detail,
            name='organization_detail',
        ),
        path('users/user/', views.users_list, name='user_list',),
        path('users/user/<str:pk>/', views.users_detail, name='users_detail'),
        path(
            'users/user/<str:pk>/password/',
            views.change_password,
            name='change_password',
        ),
        path('users/group/', views.group_list, name='group_list'),
        path('users/group/<str:pk>/', views.group_detail, name='group_detail'),
    ]
    if app_settings.USERS_AUTH_API:
        urlpatterns += [
            url(r'^user/token/', views.obtain_auth_token, name='user_auth_token')
        ]
    return urlpatterns


urlpatterns = get_api_urls()
