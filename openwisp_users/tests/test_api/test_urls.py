from types import SimpleNamespace

from django.test import SimpleTestCase

from ...api import views
from ...api.urls import get_api_urls


class TestApiUrls(SimpleTestCase):
    def test_get_api_urls_uses_overrides_and_default_fallbacks(self):
        def custom_view(request):
            return None

        view_names = {
            "organization_list": "organization_list",
            "organization_detail": "organization_detail",
            "user_list": "user_list",
            "user_detail": "user_detail",
            "change_password": "change_password",
            "email_list": "email_list",
            "email_update": "email_update",
            "organization_membership_list": "organization_membership_list",
            "organization_membership_detail": "organization_membership_detail",
            "group_list": "group_list",
            "group_detail": "group_detail",
            "user_auth_token": "obtain_auth_token",
        }
        custom_views = SimpleNamespace(
            **{
                view_name: custom_view
                for view_name in view_names.values()
                if view_name != "email_list"
            }
        )
        callbacks = {
            pattern.name: pattern.callback for pattern in get_api_urls(custom_views)
        }

        for url_name, view_name in view_names.items():
            with self.subTest(url_name=url_name):
                expected = (
                    views.email_list if view_name == "email_list" else custom_view
                )
                self.assertIs(callbacks[url_name], expected)
