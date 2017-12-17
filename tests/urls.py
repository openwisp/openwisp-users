from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path('admin/', include('admin.site.urls')),
    path('accounts/', include('allauth.urls')),
]

urlpatterns += staticfiles_urlpatterns()
