from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now, timedelta

from openwisp_users import settings as app_settings
from openwisp_users.api.serializers import (
    PasswordChangeSerializer,
    PasswordResetSerializer,
)
from openwisp_users.api.urls import get_api_urls
from openwisp_users.api.views import PasswordChangeView, PasswordResetView
from openwisp_users.base.forms import PasswordResetForm
from openwisp_users.tests.utils import TestOrganizationMixin

User = get_user_model()


class TestRestFrameworkViews(TestOrganizationMixin, TestCase):
    def setUp(self):
        cache.clear()

    def test_obtain_auth_token(self):
        self._create_user(username="tester", password="tester")
        params = {"username": "tester", "password": "tester"}
        url = reverse("users:user_auth_token")
        r = self.client.post(url, params)
        self.assertIn("token", r.data)

    @patch.object(app_settings, "USER_PASSWORD_EXPIRATION", 10)
    def test_obtain_auth_token_expired_password_success(self):
        self._create_user(
            username="tester",
            password="tester",
            password_updated=now().date() - timedelta(days=180),
        )
        params = {"username": "tester", "password": "tester"}
        url = reverse("users:user_auth_token")
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_obtain_auth_token_stamps_password_based_token(self):
        user = self._create_user(username="tester", password="tester")
        User.objects.filter(pk=user.pk).update(password_based_token=False)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, False)
        url = reverse("users:user_auth_token")
        response = self.client.post(url, {"username": "tester", "password": "tester"})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.password_based_token, True)

    def test_protected_api_mixin_view(self):
        auth_error = "Authentication credentials were not provided."
        user = self._create_user(username="tester", password="tester")
        path = reverse("users:user_detail", args=(user.pk,))
        response = self.client.get(path)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")
        self.assertEqual(response.data["detail"], auth_error)
        self.assertEqual(response.status_code, 401)

    def test_invalid_uuid_routes_return_404(self):
        invalid_uuid_paths = (
            "/api/v1/users/user/not-a-uuid/",
            "/api/v1/users/organization/not-a-uuid/",
            "/api/v1/users/user/not-a-uuid/password/",
            "/api/v1/users/user/not-a-uuid/email/",
            "/api/v1/users/user/not-a-uuid/email/1/",
        )

        for url_path in invalid_uuid_paths:
            with self.subTest(path=url_path):
                response = self.client.get(url_path)
                self.assertEqual(response.status_code, 404)


class TestGetApiUrls(TestCase):
    @patch.object(app_settings, "USERS_AUTH_API", False)
    def test_auth_routes_absent_when_users_auth_api_disabled(self):
        # Disabling OPENWISP_USERS_AUTH_API is how blocking an expired
        # password without exposing any of these local-credential routes
        # is meant to work; this proves they are actually absent, not
        # just unreachable.
        url_names = {pattern.name for pattern in get_api_urls()}
        self.assertEqual(
            url_names.isdisjoint(
                {
                    "user_auth_token",
                    "user_password_reset",
                    "user_password_reset_confirm",
                    "user_password_change",
                }
            ),
            True,
        )

    def test_password_views_define_own_serializers(self):
        """Protects recovery flows from deployment-specific REST_AUTH serializers."""
        serializers_by_view = (
            (PasswordResetView, PasswordResetSerializer),
            (PasswordChangeView, PasswordChangeSerializer),
        )
        for view, serializer in serializers_by_view:
            with self.subTest(view=view.__name__):
                self.assertIs(view.__dict__.get("serializer_class"), serializer)

    def test_password_reset_form_is_configurable(self):
        serializer = PasswordResetSerializer()
        self.assertIs(serializer.get_password_reset_form_class(), PasswordResetForm)
        with patch.object(
            app_settings,
            "PASSWORD_RESET_FORM",
            "django.contrib.auth.forms.PasswordResetForm",
        ):
            self.assertIs(
                serializer.get_password_reset_form_class(), DjangoPasswordResetForm
            )
