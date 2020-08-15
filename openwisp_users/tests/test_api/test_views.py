from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from openwisp_users.tests.utils import TestOrganizationMixin


class TestRestFrameworkViews(TestOrganizationMixin, TestCase):
    def setUp(self):
        cache.clear()

    def test_obtain_auth_token(self):
        self._create_user(username='tester', password='tester')
        params = {'username': 'tester', 'password': 'tester'}
        url = reverse('users:user_auth_token')
        r = self.client.post(url, params)
        self.assertIn('token', r.data)
