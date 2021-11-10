from django.urls import path

from . import views

urlpatterns = [
    path('member_view', views.api_member_view, name='test_api_member_view'),
    path('manager_view', views.api_manager_view, name='test_api_manager_view'),
    path('owner_view', views.api_owner_view, name='test_api_owner_view'),
    path('base_org_view', views.base_org_view, name='test_base_org_permission_view'),
    path('org_field_view', views.org_field_view, name='test_organization_field_view'),
    path('error_field_view', views.error_field_view, name='test_error_field_view'),
    path(
        'member/shelf/<str:shelf_id>/books',
        views.books_list_member_view,
        name='test_books_list_member_view',
    ),
    path(
        'manager/shelf/<str:shelf_id>/books',
        views.books_list_manager_view,
        name='test_books_list_manager_view',
    ),
    path(
        'owner/shelf/<str:shelf_id>/books',
        views.books_list_owner_view,
        name='test_books_list_owner_view',
    ),
    path(
        'member/shelf',
        views.shelf_list_member_view,
        name='test_shelf_list_member_view',
    ),
    path(
        'manager/shelf',
        views.shelf_list_manager_view,
        name='test_shelf_list_manager_view',
    ),
    path(
        'owner/shelf',
        views.shelf_list_owner_view,
        name='test_shelf_list_owner_view',
    ),
    path(
        'user/shelf/<str:shelf_id>/books',
        views.book_list_unauthorized_view,
        name='test_book_list_unauthorized_view',
    ),
    path(
        'user/shelf',
        views.shelf_list_unauthorized_view,
        name='test_shelf_list_unauthorized_view',
    ),
    path(
        'template/',
        views.template_list,
        name='test_template_list',
    ),
    path(
        'template/<int:pk>/',
        views.template_detail,
        name='test_template_detail',
    ),
    path(
        'library/',
        views.library_list,
        name='test_library_list',
    ),
    path(
        'library/<int:pk>/',
        views.library_detail,
        name='test_library_detail',
    ),
    path(
        'booknestedshelf/',
        views.book_nested_shelf,
        name='test_book_nested_shelf',
    ),
    path(
        'shelfreadonlyorg/',
        views.shelf_with_read_only_org_view,
        name='test_shelf_list_with_read_only_org',
    ),
]
