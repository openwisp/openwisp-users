import re
from html import unescape
from unittest.mock import patch
from urllib.parse import urlparse

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework import serializers

from openwisp_users.api.throttling import AuthRateThrottle
from openwisp_users.api.views import PasswordResetConfirmView
from openwisp_users.tests.utils import TestOrganizationMixin


class TestPasswordResetAPI(TestOrganizationMixin, TestCase):
    request_url = reverse_lazy("users:rest_password_reset")
    confirm_url = reverse_lazy("users:rest_password_reset_confirm")

    def setUp(self):
        cache.clear()
        self._original_rate = AuthRateThrottle.rate
        AuthRateThrottle.rate = None

    def tearDown(self):
        AuthRateThrottle.rate = self._original_rate

    def _get_reset_url_from_outbox(self):
        email = mail.outbox.pop()
        return re.search(r"https?://\S+", email.body).group(0)

    def _uid_and_token(self, reset_url):
        segment = urlparse(reset_url).path.rstrip("/").rsplit("/", 1)[-1]
        uid, token = segment.split("-", 1)
        return uid, token

    def test_reset_request_with_valid_username_sends_email(self):
        user = self._create_user(username="tester", email="tester@example.com")
        response = self.client.post(self.request_url, {"input": "tester"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"detail": "Password reset e-mail has been sent."},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_reset_request_with_valid_email_sends_email(self):
        user = self._create_user(username="tester", email="tester@example.com")
        response = self.client.post(self.request_url, {"input": user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"detail": "Password reset e-mail has been sent."},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_reset_request_with_valid_phone_number_sends_email(self):
        user = self._create_user(
            username="tester",
            email="tester@example.com",
            phone_number="+12025551234",
        )
        response = self.client.post(self.request_url, {"input": "+12025551234"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"detail": "Password reset e-mail has been sent."},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_reset_request_with_unknown_identifier_is_indistinguishable(self):
        self._create_user(username="tester", email="tester@example.com")
        known_user_response = self.client.post(self.request_url, {"input": "tester"})
        mail.outbox.clear()

        unknown_user_response = self.client.post(
            self.request_url, {"input": "does-not-exist"}
        )
        self.assertEqual(
            unknown_user_response.status_code, known_user_response.status_code
        )
        self.assertEqual(unknown_user_response.data, known_user_response.data)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_request_email_has_plain_and_html_parts_with_matching_link(self):
        self._create_user(username="tester", email="tester@example.com")
        response = self.client.post(self.request_url, {"input": "tester"})
        self.assertEqual(response.status_code, 200)
        email = mail.outbox[0]
        plain_url = re.search(r"https?://\S+", email.body).group(0)
        plain_uid, plain_token = self._uid_and_token(plain_url)
        # Verify HTML email
        self.assertEqual(len(email.alternatives), 1)
        html_body = email.alternatives[0][0]
        self.assertEqual(email.alternatives[0][1], "text/html")
        html_url = re.search(r'href="([^"]+)" class="btn"', html_body).group(1)
        html_uid, html_token = self._uid_and_token(unescape(html_url))
        self.assertEqual(plain_uid, html_uid)
        self.assertEqual(plain_token, html_token)

    def test_reset_email_cta_url_is_followable_with_get(self):
        self._create_user(username="tester", email="tester@example.com")
        self.client.post(self.request_url, {"input": "tester"})
        reset_url = self._get_reset_url_from_outbox()
        response = self.client.get(urlparse(reset_url).path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Change Password")

    def test_reset_confirm_with_valid_uid_and_token_changes_password(self):
        user = self._create_user(username="tester", email="tester@example.com")
        self.client.post(self.request_url, {"input": "tester"})
        reset_url = self._get_reset_url_from_outbox()
        uid, token = self._uid_and_token(reset_url)
        response = self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": token,
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.check_password("newpassword123"), True)

    def test_reset_confirm_with_invalid_token_returns_400(self):
        user = self._create_user(username="tester", email="tester@example.com")
        self.client.post(self.request_url, {"input": "tester"})
        reset_url = self._get_reset_url_from_outbox()
        uid, _token = self._uid_and_token(reset_url)
        response = self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": "invalid-token",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.check_password("newpassword123"), False)

    def test_reset_confirm_validate_user_hook_is_called_and_can_reject(self):
        user = self._create_user(username="tester", email="tester@example.com")
        self.client.post(self.request_url, {"input": "tester"})
        reset_url = self._get_reset_url_from_outbox()
        uid, token = self._uid_and_token(reset_url)
        with patch.object(
            PasswordResetConfirmView,
            "validate_user",
            side_effect=serializers.ValidationError("not allowed"),
        ) as mocked:
            response = self.client.post(
                self.confirm_url,
                {
                    "uid": uid,
                    "token": token,
                    "new_password1": "newpassword123",
                    "new_password2": "newpassword123",
                },
            )
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.args[0].pk, user.pk)
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.check_password("newpassword123"), False)

    def test_reset_request_inactive_user_does_not_receive_email(self):
        user = self._create_user(username="tester", email="tester@example.com")
        user.is_active = False
        user.save()
        response = self.client.post(self.request_url, {"input": "tester"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_request_user_with_unusable_password_does_not_receive_email(self):
        user = self._create_user(username="tester", email="tester@example.com")
        user.set_unusable_password()
        user.save()
        response = self.client.post(self.request_url, {"input": "tester"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)


class TestPasswordChangeAPI(TestOrganizationMixin, TestCase):
    change_url = reverse_lazy("users:rest_password_change")

    def test_password_change_with_valid_current_password_succeeds(self):
        user = self._create_user(username="tester", password="tester")
        self.client.force_login(user)
        response = self.client.post(
            self.change_url,
            {
                "old_password": "tester",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.check_password("newpassword123"), True)

    def test_password_change_with_wrong_current_password_fails(self):
        user = self._create_user(username="tester", password="tester")
        self.client.force_login(user)
        response = self.client.post(
            self.change_url,
            {
                "old_password": "wrong-password",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.check_password("tester"), True)

    def test_password_change_without_old_password_fails(self):
        user = self._create_user(username="tester", password="tester")
        self.client.force_login(user)
        response = self.client.post(
            self.change_url,
            {
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.data)
        user.refresh_from_db()
        self.assertEqual(user.check_password("tester"), True)
