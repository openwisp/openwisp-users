from django.urls import path

from . import views

urlpatterns = [
    path('member_view', views.api_member_view, name='test_api_member_view'),
    path('manager_view', views.api_manager_view, name='test_api_manager_view'),
    path('owner_view', views.api_owner_view, name='test_api_owner_view'),
    path('base_org_view', views.base_org_view, name='test_base_org_permission_view'),
    path('org_field_view', views.org_field_view, name='test_organization_field_view'),
    path('error_field_view', views.error_field_view, name='test_error_field_view'),
]
