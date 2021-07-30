from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.tests import AssertNumQueriesSubTestMixin
from swapper import load_model

from ..utils import TestOrganizationMixin

Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()
Group = load_model('openwisp_users', 'Group')


class TestUsersApi(
    AssertNumQueriesSubTestMixin, TestOrganizationMixin, TestCase,
):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            username='administrator', password='admin', email='test@test.org'
        )
        self.client.force_login(user)

    # Tests for Organization Model API endpoints
    def test_organization_list_api(self):
        path = reverse('users:organization_list')
        with self.assertNumQueries(3):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)

    def test_organization_list_nonsuperuser_api(self):
        user = self._create_user()
        view_perm = Permission.objects.filter(codename='view_organization')
        user.user_permissions.add(*view_perm)
        self.client.force_login(user)
        path = reverse('users:organization_list')
        with self.assertNumQueries(4):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 0)
        self.assertEqual(Organization.objects.count(), 1)

    def test_organization_post_api(self):
        path = reverse('users:organization_list')
        data = {'name': 'test-org', 'slug': 'test-org'}
        with self.assertNumQueries(6):
            r = self.client.post(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Organization.objects.count(), 2)

    def test_organization_detail_api(self):
        org1 = self._get_org()
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(2):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 200)

    def test_organization_detail_nonsuperuser_api(self):
        user = self._create_user()
        view_perm = Permission.objects.filter(codename='view_organization')
        user.user_permissions.add(*view_perm)
        self.client.force_login(user)
        org1 = self._get_org()
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(4):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 404)

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
            r = self.client.put(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['name'], 'test org change')
        self.assertEqual(r.data['description'], 'testing PUT')

    def test_organization_patch_api(self):
        org1 = self._get_org()
        self.assertEqual(org1.name, 'test org')
        path = reverse('users:organization_detail', args=(org1.pk,))
        data = {
            'name': 'test org change',
        }
        with self.assertNumQueries(4):
            r = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['name'], 'test org change')

    def test_organization_delete_api(self):
        org1 = self._create_org(name='test org 2')
        self.assertEqual(Organization.objects.count(), 2)
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(9):
            r = self.client.delete(path)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Organization.objects.count(), 1)

    def test_get_organization_for_org_manager(self):
        user1 = self._create_user(username='user1', email='user1@email.com')
        org1 = self._create_org(name='org1')
        self._create_org_user(user=user1, organization=org1, is_admin=True)
        view_perm = Permission.objects.filter(codename='view_organization')
        user1.user_permissions.add(*view_perm)
        self.client.force_login(user1)

        with self.subTest('Organization List'):
            path = reverse('users:organization_list')
            with self.assertNumQueries(5):
                r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.data['count'], 1)

        with self.subTest('Organization Detail'):
            path = reverse('users:organization_detail', args=(org1.pk,))
            with self.assertNumQueries(4):
                r = self.client.get(path)
            self.assertEqual(r.status_code, 200)

    # Tests for Group Model API endpoints
    def test_get_group_list_403(self):
        user = self._create_user(username='user1', email='user1@email.com')
        self.client.force_login(user)
        path = reverse('users:group_list')
        with self.assertNumQueries(3):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 403)

    def test_get_group_list_api(self):
        path = reverse('users:group_list')
        with self.assertNumQueries(18):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 2)

    def test_create_group_list_api(self):
        path = reverse('users:group_list')
        data = {'name': 'test-group', 'permissions': []}
        with self.assertNumQueries(5):
            r = self.client.post(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data.pop('id'), 3)
        self.assertEqual(r.data, data)

    def test_get_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
        with self.assertNumQueries(3):
            r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['id'], 1)
        self.assertEqual(r.data['name'], 'Operator')
        self.assertEqual(r.data['permissions'], [])

    def test_put_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
        data = {'name': 'test-Operator', 'permissions': []}
        with self.assertNumQueries(7):
            r = self.client.put(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['id'], 1)
        self.assertEqual(r.data['name'], 'test-Operator')

    def test_patch_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
        data = {'permissions': [1]}
        with self.assertNumQueries(10):
            r = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data['permissions'], ['1: emailaddress | Can add email address']
        )

    def test_delete_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
        with self.assertNumQueries(5):
            r = self.client.delete(path)
        self.assertEqual(r.status_code, 204)
        self.assertIsNone(r.data)

    # Test Change Password endpoints
    def test_with_wrong_password(self):
        client = auth.get_user(self.client)
        path = reverse('users:change_password', args=(client.pk,))
        data = {'old_password': 'wrong', 'new_password': 'super1234'}
        with self.assertNumQueries(4):
            response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['old_password'], ['You have entered a wrong password.']
        )

    def test_change_password_of_superuser_by_superuser(self):
        client = auth.get_user(self.client)
        path = reverse('users:change_password', args=(client.pk,))
        data = {'old_password': 'admin', 'new_password': 'super1234'}
        with self.assertNumQueries(5):
            response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Password updated successfully')

    def test_change_password_of_other_user_by_superuser(self):
        org1 = self._create_org(name='org1')
        org1_user = self._create_user(username='org1_user', email='org1_user@test.com')
        self._create_org_user(organization=org1, user=org1_user)

    def test_change_password_org_manager(self):
        # Org managers should be able to update
        # passwords of his org. users
        org1 = self._create_org(name='org1')
        org1_manager = self._create_user(
            username='org1_manager', password='test123', email='org1_manager@test.com'
        )
        self._create_org_user(organization=org1, user=org1_manager, is_admin=True)
        administrator = Group.objects.get(name='Administrator')
        org1_manager.groups.add(administrator)

        org1_user = self._create_user(
            username='org1_user',
            password='test321',
            email='org1_user@test.com',
            is_staff=True,
        )
        self._create_org_user(organization=org1, user=org1_user)
        org1_user.groups.add(administrator)

        with self.subTest('Change password of org manager by manager'):
            self.client.force_login(org1_manager)
            path = reverse('users:change_password', args=(org1_manager.pk,))
            data = {'old_password': 'test123', 'new_password': 'test1234'}
            with self.assertNumQueries(8):
                response = self.client.put(path, data, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'], 'Password updated successfully')

        with self.subTest('Change password of org user by org manager'):
            org1_manager.refresh_from_db()
            self.client.force_login(org1_manager)
            path = reverse('users:change_password', args=(org1_user.pk,))
            data = {'old_password': 'test321', 'new_password': 'test1234'}
            with self.assertNumQueries(8):
                response = self.client.put(path, data, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'], 'Password updated successfully')

        with self.subTest('change password of org user by itself'):
            org1_user.refresh_from_db()
            self.client.force_login(org1_user)
            path = reverse('users:change_password', args=(org1_user.pk,))
            data = {'old_password': 'test1234', 'new_password': 'test1342'}
            with self.assertNumQueries(8):
                response = self.client.put(path, data, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['message'], 'Password updated successfully')
