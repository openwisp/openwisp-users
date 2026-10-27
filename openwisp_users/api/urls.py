from django.urls import path

from openwisp_users import settings as app_settings

from . import views


def get_api_urls(api_views=None):
    urlpatterns = []
    if api_views is None:
        api_views = views

    def get_view(name):
        """Fall back to the standard view when a custom view is unavailable."""
        return getattr(api_views, name, getattr(views, name))

    urlpatterns += [
        path(
            "users/organization/",
            get_view("organization_list"),
            name="organization_list",
        ),
        path(
            "users/organization/<uuid:pk>/",
            get_view("organization_detail"),
            name="organization_detail",
        ),
        path(
            "users/user/",
            get_view("user_list"),
            name="user_list",
        ),
        path("users/user/<uuid:pk>/", get_view("user_detail"), name="user_detail"),
        path(
            "users/user/<uuid:pk>/password/",
            get_view("change_password"),
            name="change_password",
        ),
        path(
            "users/user/<uuid:pk>/email/",
            get_view("email_list"),
            name="email_list",
        ),
        path(
            "users/user/<uuid:pk>/email/<int:email_id>/",
            get_view("email_update"),
            name="email_update",
        ),
        path(
            "users/user/<uuid:pk>/organization-membership/",
            get_view("organization_membership_list"),
            name="organization_membership_list",
        ),
        path(
            "users/user/<uuid:pk>/organization-membership/<uuid:org_id>/",
            get_view("organization_membership_detail"),
            name="organization_membership_detail",
        ),
        path("users/group/", get_view("group_list"), name="group_list"),
        path("users/group/<int:pk>/", get_view("group_detail"), name="group_detail"),
    ]
    if app_settings.USERS_AUTH_API:
        urlpatterns += [
            path("users/token/", get_view("obtain_auth_token"), name="user_auth_token"),
            path(
                "users/password/reset/",
                get_view("password_reset"),
                name="user_password_reset",
            ),
            path(
                "users/password/reset/confirm/",
                get_view("password_reset_confirm"),
                name="user_password_reset_confirm",
            ),
            path(
                "users/user/password/change/",
                get_view("password_change"),
                name="user_password_change",
            ),
        ]
    return urlpatterns


urlpatterns = get_api_urls()
app_name = "users"
