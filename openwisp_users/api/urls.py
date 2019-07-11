from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^orgs/$',
        views.list_orgs,
        name='list_orgs'),
    url(r'^orgs/(?P<pk>[^/]+)/$',
        views.org_detail,
        name='org_detail'),
]
