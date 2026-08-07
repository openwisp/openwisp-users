from django.core.cache import cache
from django.urls import reverse

from openwisp_users.api.throttling import AuthRateThrottle

from . import APITestCase


class RatelimitTests(APITestCase):
    def setUp(self):
        cache.clear()
        self._create_operator()
        self._original_rate = AuthRateThrottle.rate

    def tearDown(self):
        AuthRateThrottle.rate = self._original_rate
        cache.clear()

    def test_auth_rate_throttle(self):
        AuthRateThrottle.rate = "1/day"
        url = reverse("users:user_auth_token")
        data = {"username": "operator", "password": "tester"}
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 200)
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 429)

    def test_authenticated_password_change_is_rate_limited(self):
        AuthRateThrottle.rate = "1/day"
        user = self._get_operator()
        self.client.force_login(user)
        url = reverse("users:rest_password_change")
        data = {
            "old_password": "wrong-password",
            "new_password1": "newpassword123",
            "new_password2": "newpassword123",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 429)
