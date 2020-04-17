from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from openwisp_users.api.throttling import AuthRateThrottle
from openwisp_users.tests.utils import TestMultitenantAdminMixin


class RatelimitTests(TestMultitenantAdminMixin, TestCase):
    def setUp(self):
        cache.clear()
        self._create_operator()

    def test_auth_rate_throttle(self):
        AuthRateThrottle.rate = '1/day'
        url = reverse('api-token-auth')
        data = {"username": "operator", "password": "tester"}
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 200)
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 429)
