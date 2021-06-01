from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from openwisp_users.api.throttling import AuthRateThrottle

from ..models import Template
from .mixins import TestMultitenancyMixin

User = get_user_model()
Group = load_model('openwisp_users', 'Group')
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


class TestPermissionClasses(TestMultitenancyMixin, TestCase):
    def setUp(self):
        AuthRateThrottle.rate = 0
        self.template_model = Template
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

    def _get_auth_template(self, user, org1):
        OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
        self.client.force_login(user)
        token = self._obtain_auth_token(user)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        t1 = self._create_template(organization=org1)
        return (auth, t1)

    def test_view_permission_with_operator(self):
        user = self._get_user()
        operator_group = Group.objects.filter(name='Operator')
        user.groups.set(operator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest('Get Template List'):
            response = self.client.get(reverse('test_template_list'), **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest('Get Template Detail'):
            response = self.client.get(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 403)

    def test_view_permission_with_administrator(self):
        user = self._get_user()
        administrator_group = Group.objects.get(name='Administrator')
        change_perm = Permission.objects.get(codename='change_template')
        administrator_group.permissions.add(change_perm)
        user.groups.add(administrator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest('Get Template List'):
            response = self.client.get(reverse('test_template_list'), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Get Template Detail'):
            response = self.client.get(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)
        permissions = administrator_group.permissions.values_list('codename', flat=True)
        self.assertFalse('view_template' in permissions)
        self.assertTrue('change_template' in permissions)

    def test_view_permission_with_operator_having_view_perm(self):
        user = self._get_user()
        operator_group = Group.objects.get(name='Operator')
        view_perm = Permission.objects.get(codename='view_template')
        operator_group.permissions.add(view_perm)
        user.groups.add(operator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest('Get Template List'):
            response = self.client.get(reverse('test_template_list'), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Get Template Detail'):
            response = self.client.get(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)
        with self.subTest('Change Template Detail'):
            data = {'name': 'change-template'}
            response = self.client.patch(
                reverse('test_template_detail', args=[t1.pk]), data, **auth
            )
            self.assertEqual(response.status_code, 403)
        with self.subTest('Delete Template'):
            response = self.client.delete(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 403)

    def test_view_django_model_permission_with_view_perm(self):
        user = self._get_user()
        user_permissions = Permission.objects.filter(codename='view_template')
        user.user_permissions.add(*user_permissions)
        user.organizations_dict  # force caching
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest('Get Template List'):
            response = self.client.get(reverse('test_template_list'), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Get Template Detail'):
            response = self.client.get(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)

    def test_view_django_model_permission_with_change_perm(self):
        user = self._get_user()
        user_permissions = Permission.objects.filter(codename='change_template')
        user.user_permissions.add(*user_permissions)
        user.organizations_dict  # force caching
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest('Get Template List'):
            response = self.client.get(reverse('test_template_list'), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest('Get Template Detail'):
            response = self.client.get(
                reverse('test_template_detail', args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)
