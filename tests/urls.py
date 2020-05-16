from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('openwisp_users.accounts.urls')),
    url(r'^api/v1/', include('openwisp_users.api.urls')),
    url(r'^api/v1/', include('openwisp_utils.api.urls')),
]

urlpatterns += staticfiles_urlpatterns()
