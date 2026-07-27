from unittest.mock import patch

from django.contrib.auth import get_user, get_user_model
from django.test import TestCase, modify_settings
from django.urls import reverse
from django.utils.timezone import now, timedelta
from rest_framework.authtoken.models import Token

from .. import settings as app_settings
from ..auth import PASSWORD, SESSION_KEY
from .utils import TestOrganizationMixin

User = get_user_model()


class TestPasswordExpirationMiddleware(TestOrganizationMixin, TestCase):
    @modify_settings(
        MIDDLEWARE={
            "remove": ["openwisp_users.middleware.PasswordExpirationMiddleware"]
        }
    )
    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_queries_middleware_absent(self):
        admin = self._create_admin()
        with self.assertNumQueries(2):
            response = self.client.post(
                reverse("admin:login"),
                data={"username": admin.username, "password": "tester"},
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/admin/")
        with self.assertNumQueries(1):
            self.client.force_login(admin)

    @modify_settings(
        MIDDLEWARE={
            "append": ["openwisp_users.middleware.PasswordExpirationMiddleware"]
        }
    )
    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_queries_middleware_present(self):
        admin = self._create_admin(password_updated=now().date() - timedelta(days=180))
        with self.assertNumQueries(2):
            response = self.client.post(
                reverse("admin:login"),
                data={"username": admin.username, "password": "tester"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/password/change/?next=/admin/")
        self.assertEqual(self.client.session[SESSION_KEY], PASSWORD)

        with self.assertNumQueries(1):
            self.client.force_login(admin)

    def _login_expired_admin(self):
        admin = self._create_admin(password_updated=now().date() - timedelta(days=180))
        self.client.force_login(admin)
        return admin

    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_expired_password_staff_user_can_still_logout(self):
        self._login_expired_admin()
        response = self.client.post(reverse("admin:logout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/logged_out.html")
        self.assertEqual(get_user(self.client).is_authenticated, False)

    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_expired_password_user_nonexistent_url_returns_404(self):
        self._login_expired_admin()
        response = self.client.get("/this-path-does-not-exist/")
        self.assertEqual(response.status_code, 404)

    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_expired_password_session_blocks_rest_request_before_view_runs(self):
        self._login_expired_admin()
        self.assertEqual(User.objects.count(), 1)
        response = self.client.post(
            reverse("users:user_list"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.json()["code"], "password_expired")
        self.assertEqual(
            response.json()["detail"],
            "Your password has expired. Update it to continue.",
        )
        self.assertEqual(
            response.json()["api_password_change_url"],
            response.wsgi_request.build_absolute_uri(
                reverse("users:rest_password_change")
            ),
        )

    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_expired_password_session_can_use_rest_password_change(self):
        admin = self._login_expired_admin()
        response = self.client.put(
            reverse("users:rest_password_change"),
            data={
                "current_password": "tester",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        admin.refresh_from_db()
        self.assertEqual(admin.check_password("newpassword123"), True)
        self.assertEqual(admin.has_password_expired(), False)

    @patch.object(app_settings, "STAFF_USER_PASSWORD_EXPIRATION", 10)
    def test_expired_password_session_bearer_request_not_blocked_for_existing_token(
        self,
    ):
        admin = self._create_admin()
        token = Token.objects.create(user=admin)
        admin.password_updated = now().date() - timedelta(days=180)
        admin.save()
        response = self.client.get(
            reverse("users:user_list"),
            HTTP_AUTHORIZATION=f"Bearer {token.key}",
        )
        self.assertEqual(response.status_code, 200)
