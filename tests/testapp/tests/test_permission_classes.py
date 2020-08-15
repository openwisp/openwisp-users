from django.test import TestCase
from django.urls import reverse

from openwisp_users.api.throttling import AuthRateThrottle

from .mixins import TestMultitenancyMixin


class TestPermissionClasses(TestMultitenancyMixin, TestCase):
    def setUp(self):
        AuthRateThrottle.rate = 0
        self.member_url = reverse('test_api_member_view')
        self.manager_url = reverse('test_api_manager_view')
        self.owner_url = reverse('test_api_owner_view')

    def test_operator_none(self):
        self._get_operator()
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.subTest('Organization Member'):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest('Organization Manager'):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest('Organization Owner'):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_member(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.subTest('Organization Member'):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Manager'):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest('Organization Owner'):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_manager(self):
        operator = self._get_operator()
        # First user is automatically owner, so created dummy
        # user to keep operator as manager only.
        self._create_org_user(user=self._get_user(), is_admin=True)
        self._create_org_user(user=operator, is_admin=True)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.subTest('Organization Member'):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Manager'):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Owner'):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_owner(self):
        operator = self._get_operator()
        # First user is automatically owner
        self._create_org_user(user=operator, is_admin=True)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.subTest('Organization Member'):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Manager'):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Owner'):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 200)

    def test_superuser(self):
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.subTest('Organization Member'):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Manager'):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Organization Owner'):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 200)

    def test_base_org_perm_fails(self):
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        base_org_permissions_url = reverse('test_base_org_permission_view')
        with self.assertRaises(NotImplementedError) as error:
            self.client.get(base_org_permissions_url, **auth)
        self.assertIn('Please use one of the child classes', str(error.exception))

    def test_organization_field_with_parent(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('test_organization_field_view'), **auth)
        self.assertEqual(response.status_code, 200)

    def test_organization_field_with_errored_parent(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        with self.assertRaises(AttributeError) as error:
            self.client.get(reverse('test_error_field_view'), **auth)
        self.assertIn('Organization not found', str(error.exception))
