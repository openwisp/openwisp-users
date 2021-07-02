from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.tests import AssertNumQueriesSubTestMixin
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')


class TestUsersApi(
    AssertNumQueriesSubTestMixin, TestCase,
):
    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        self.client.force_login(user)

    def test_organization_list_api(self):
        path = reverse('users:organization_list')
        with self.assertNumQueries(3):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_organization_post_api(self):
        path = reverse('users:organization_list')
        data = {'name': 'test-org', 'slug': 'test-org'}
        with self.assertNumQueries(6):
            response = self.client.post(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Organization.objects.count(), 2)
