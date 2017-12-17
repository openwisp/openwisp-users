from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path('admin/', include('adminsite.urls')),
    path('accounts/', include('allauth.urls')),
]

urlpatterns += staticfiles_urlpatterns()
