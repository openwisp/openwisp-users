from allauth.account.models import EmailAddress
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
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


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
        with self.assertNumQueries(3):
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
        with self.assertNumQueries(6):
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
        with self.assertNumQueries(5):
            r = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['name'], 'test org change')

    def test_organization_delete_api(self):
        org1 = self._create_org(name='test org 2')
        self.assertEqual(Organization.objects.count(), 2)
        path = reverse('users:organization_detail', args=(org1.pk,))
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
            with self.assertNumQueries(5):
                r = self.client.get(path)
            self.assertEqual(r.status_code, 200)

    def test_change_organizationowner_for_org(self):
        user1 = self._create_user(username='user1', email='user1@email.com')
        user2 = self._create_user(username='user2', email='user2@email.com')
        org1 = self._create_org(name='org1')
        org1_user1 = self._create_org_user(user=user1, organization=org1)
        org1_user2 = self._create_org_user(user=user2, organization=org1)
        self._create_org_owner(organization_user=org1_user1, organization=org1)
        self.assertEqual(org1.owner.organization_user.id, org1_user1.id)
        path = reverse('users:organization_detail', args=(org1.pk,))
        data = {'owner': {'organization_user': org1_user2.id}}
        with self.assertNumQueries(26):
            response = self.client.patch(path, data, content_type='application/json')
        org1.refresh_from_db()
        self.assertEqual(org1.owner.organization_user.id, org1_user2.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['owner']['organization_user'], org1_user2.id)

    def test_orguser_filter_for_organization_detail(self):
        user1 = self._create_user(username='user1', email='user1@email.com')
        user2 = self._create_user(username='user2', email='user2@email.com')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self._create_org_user(user=user1, organization=org1, is_admin=True)
        self._create_org_user(user=user2, organization=org2)
        change_perm = Permission.objects.filter(codename='change_organization')
        user1.user_permissions.add(*change_perm)
        self.client.force_login(user1)
        path = reverse('users:organization_detail', args=(org1.pk,))
        with self.assertNumQueries(7):
            response = self.client.get(path, {'format': 'api'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user1</option>')
        self.assertNotContains(response, 'user2</option>')

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
        r = self.client.put(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['id'], 1)
        self.assertEqual(r.data['name'], 'test-Operator')

    def test_patch_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
        data = {'permissions': [1]}
        r = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data['permissions'], ['1: emailaddress | Can add email address']
        )

    def test_delete_group_detail_api(self):
        path = reverse('users:group_detail', args='1')
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

    # Tests for users email update endpoints
    def test_get_email_api(self):
        user = self._get_user()
        path = reverse('users:email_update', args=(user.pk,))
        with self.assertNumQueries(4):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@tester.com')
        self.assertEqual(response.data['verified'], True)
        self.assertEqual(response.data['primary'], True)

    def test_get_user_email_from_another_org_404(self):
        org1 = self._get_org()
        admin = self._create_admin(email='admin@test.com')
        self._create_org_user(organization=org1, user=admin)
        self.client.force_login(admin)
        org2 = self._create_org(name='org2')
        user2 = self._create_user(
            username='user2', is_staff=True, email='user2@gmail.com'
        )
        org2user = self._create_org_user(organization=org2, user=user2)
        path = reverse('users:email_update', args=(org2user.pk,))
        with self.assertNumQueries(2):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_not_existing_email_200(self):
        admin = self._create_admin(email='')
        self.client.force_login(admin)
        path = reverse('users:email_update', args=(admin.pk,))
        with self.assertNumQueries(3):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'Email not found')

    def test_add_new_email_for_emailnotfound_user(self):
        admin = self._create_admin(email='')
        self.client.force_login(admin)
        self.assertEqual(admin.email, '')
        path = reverse('users:email_update', args=(admin.pk,))
        data = {'email': 'admin@tester.com', 'verified': True, 'primary': True}
        with self.assertNumQueries(13):
            response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        email_obj = EmailAddress.objects.get(user=admin)
        self.assertEqual(email_obj.email, 'admin@tester.com')

    def test_put_email_api(self):
        user = self._get_user()
        path = reverse('users:email_update', args=(user.pk,))
        email_obj = EmailAddress.objects.get(user=user)
        self.assertTrue(email_obj.verified)
        self.assertTrue(email_obj.primary)
        self.assertEqual(email_obj.email, 'test@tester.com')
        data = {'email': 'changetest@tester.com', 'verified': False, 'primary': False}
        with self.assertNumQueries(8):
            response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        email_obj.refresh_from_db()
        self.assertEqual(email_obj.email, 'changetest@tester.com')
        self.assertEqual(response.data['email'], 'changetest@tester.com')
        self.assertFalse(response.data['primary'])
        self.assertFalse(response.data['verified'])

    def test_patch_email_api(self):
        user = self._get_user()
        self.assertEqual(user.email, 'test@tester.com')
        path = reverse('users:email_update', args=(user.pk,))
        data = {'email': 'newemail@test.com'}
        with self.assertNumQueries(8):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'newemail@test.com')
        email_obj = EmailAddress.objects.get(user=user)
        self.assertEqual(email_obj.email, 'newemail@test.com')

    def test_with_wrong_email_format_api_400(self):
        user = self._get_user()
        path = reverse('users:email_update', args=(user.pk,))
        data = {'email': 'email.com'}
        with self.assertNumQueries(5):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Enter a valid email address.', str(response.content))

    def test_delete_email_api(self):
        user = self._get_user()
        path = reverse('users:email_update', args=(user.pk,))
        with self.assertNumQueries(5):
            response = self.client.delete(path)
        self.assertEqual(response.status_code, 204)

    # Tests for superuser's User API endpoints
    def test_get_user_list_api(self):
        path = reverse('users:user_list')
        with self.assertNumQueries(5):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_create_user_list_api(self):
        self.assertEqual(User.objects.count(), 1)
        path = reverse('users:user_list')
        data = {
            'username': 'tester',
            'email': 'tester@test.com',
            'password': 'password123',
        }
        with self.assertNumQueries(14):
            response = self.client.post(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data['groups'], [])
        self.assertEqual(response.data['organization_users'], [])
        self.assertEqual(response.data['username'], 'tester')
        self.assertEqual(response.data['email'], 'tester@test.com')
        self.assertEqual(response.data['is_active'], True)

    def test_post_with_empty_form_api_400(self):
        path = reverse('users:user_list')
        with self.assertNumQueries(1):
            response = self.client.post(path, {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_get_user_detail_api(self):
        user = self._get_user()
        path = reverse('users:user_detail', args=(user.pk,))
        with self.assertNumQueries(5):
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(user.id))
        self.assertEqual(response.data['email'], 'test@tester.com')

    def test_put_user_detail_api(self):
        user = self._get_user()
        org1 = self._get_org()
        path = reverse('users:user_detail', args=(user.pk,))
        data = {
            'username': 'tester',
            'first_name': 'Tester',
            'last_name': 'Tester',
            'email': 'test@tester.com',
            'bio': '',
            'url': '',
            'company': '',
            'location': '',
            'phone_number': None,
            'birth_date': '1987-03-23',
            'notes': '',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
            'groups': [],
            'user_permissions': [],
            'organization_users': [{'is_admin': False, 'organization': org1.pk}],
        }
        self.assertEqual(OrganizationUser.objects.count(), 0)
        response = self.client.put(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OrganizationUser.objects.count(), 1)
        self.assertEqual(
            response.data['organization_users'][0]['organization'], org1.pk
        )

    def test_patch_user_detail_api(self):
        user = self._get_user()
        path = reverse('users:user_detail', args=(user.pk,))
        data = {'username': 'changetestuser'}
        with self.assertNumQueries(10):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'changetestuser')

    def test_assign_user_to_groups_api(self):
        user = self._get_user()
        self.assertEqual(user.groups.count(), 0)
        path = reverse('users:user_detail', args=(user.pk,))
        data = {'groups': [1]}
        with self.assertNumQueries(15):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(response.data['groups'], [1])

    def test_assign_permission_to_user_api(self):
        user = self._get_user()
        self.assertEqual(user.permissions, set())
        path = reverse('users:user_detail', args=(user.pk,))
        data = {'user_permissions': [1, 2]}
        with self.assertNumQueries(16):
            response = self.client.patch(path, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        perm = {'account.change_emailaddress', 'account.add_emailaddress'}
        self.assertEqual(user.permissions, perm)
        self.assertEqual(response.data['user_permissions'], [1, 2])

    def test_delete_user_api(self):
        user = self._get_user()
        path = reverse('users:user_detail', args=(user.pk,))
        response = self.client.delete(path)
        self.assertEqual(response.status_code, 204)
