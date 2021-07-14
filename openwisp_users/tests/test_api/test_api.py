from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.tests import AssertNumQueriesSubTestMixin
from swapper import load_model

from ..utils import TestOrganizationMixin

Organization = load_model('openwisp_users', 'Organization')


class TestUsersApi(
    AssertNumQueriesSubTestMixin, TestOrganizationMixin, TestCase,
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

    def test_organization_list_nonsuperuser_api(self):
        user = self._create_user()
        self.client.force_login(user)
        path = reverse('users:organization_list')
        with self.assertNumQueries(1):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(Organization.objects.count(), 1)

    def test_organization_post_api(self):
        path = reverse('users:organization_list')
        data = {'name': 'test-org', 'slug': 'test-org'}
        with self.assertNumQueries(6):
            response = self.client.post(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Organization.objects.count(), 2)

    def test_organization_detail_api(self):
        org1 = self._get_org()
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(2):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_organization_detail_nonsuperuser_api(self):
        user = self._create_user()
        self.client.force_login(user)
        org1 = self._get_org()
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(1):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_organization_put_api(self):
        org1 = self._get_org()
        self.assertEqual(org1.name, 'test org')
        self.assertEqual(org1.description, '')
        path = reverse('users:organization_detail', args=(org1.pk,))
        data = {
            'name': 'test org change',
            'is_active': False,
            'slug': 'test-org-change',
            'description': 'testing PUT',
            'email': 'testorg@test.com',
            'url': '',
        }
        with self.assertNumQueries(5):
            response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'test org change')
        self.assertEqual(response.data['description'], 'testing PUT')

    def test_organization_patch_api(self):
        org1 = self._get_org()
        self.assertEqual(org1.name, 'test org')
        path = reverse('users:organization_detail', args=(org1.pk,))
        data = {
            'name': 'test org change',
        }
        with self.assertNumQueries(4):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'test org change')

    def test_organization_delete_api(self):
        org1 = self._create_org(name='test org 2')
        self.assertEqual(Organization.objects.count(), 2)
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(9):
            response = self.client.delete(path)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Organization.objects.count(), 1)
