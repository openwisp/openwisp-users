import os

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from openwisp_users.api.urls import get_api_urls

if os.environ.get('SAMPLE_APP', False):
    # We don't need to set any value for api_views
    # if we don't want to extend the views (optional).
    api_views = None
else:
    # If we want to extend the views, we call these views
    from .sample_users import views as api_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('openwisp_users.accounts.urls')),
    url(r'^api/v1/', include((get_api_urls(api_views), 'users'), namespace='users')),
    url(r'^api/v1/', include('openwisp_utils.api.urls')),
    # Only for testing 'testapp'
    url(r'^testing', include('testapp.urls')),
]

urlpatterns += staticfiles_urlpatterns()
