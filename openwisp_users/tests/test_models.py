from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from swapper import load_model

from .utils import TestOrganizationMixin

OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
Group = load_model('openwisp_users', 'Group')
User = get_user_model()


class TestUsers(TestOrganizationMixin, TestCase):
    user_model = User

    def test_create_superuser_email(self):
        user = User.objects.create_superuser(
            username='tester', password='tester', email='test@superuser.com'
        )
        self.assertEqual(user.emailaddress_set.count(), 1)
        self.assertEqual(user.emailaddress_set.first().email, 'test@superuser.com')

    def test_create_superuser_email_empty(self):
        user = User.objects.create_superuser(
            username='tester', password='tester', email=''
        )
        self.assertEqual(user.emailaddress_set.count(), 0)

    def test_unique_email_validation(self):
        self._create_user(username='user1', email='same@gmail.com')
        options = {'username': 'user2', 'email': 'same@gmail.com', 'password': 'pass1'}
        u = self.user_model(**options)
        with self.assertRaises(ValidationError):
            u.full_clean()

    def test_create_user_without_email(self):
        options = {
            'username': 'testuser',
            'password': 'test1',
        }
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)

    def test_organizations_pk(self):
        user = self._create_user(username='organizations_pk')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self._create_org(name='org3')
        OrganizationUser.objects.create(user=user, organization=org1)
        OrganizationUser.objects.create(user=user, organization=org2)
        self.assertIn((org1.pk,), user.organizations_pk)
        self.assertEqual(len(user.organizations_pk), 2)

    def test_organizations_pk_empty(self):
        user = self._create_user(username='organizations_pk')
        self.assertEqual(len(user.organizations_pk), 0)

    def test_organizations_dict(self):
        user = self._create_user(username='organizations_pk')
        self.assertEqual(user.organizations_dict, {})
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self._create_org(name='org3')
        ou1 = OrganizationUser.objects.create(
            user=user, organization=org1, is_admin=True
        )
        ou2 = OrganizationUser.objects.create(user=user, organization=org2)

        expected = {
            str(org1.pk): {'is_admin': ou1.is_admin, 'is_owner': True},
            str(org2.pk): {'is_admin': ou2.is_admin, 'is_owner': False},
        }
        self.assertEqual(user.organizations_dict, expected)
        self.assertEqual(len(user.organizations_dict), 2)

        ou2.delete()
        self.assertEqual(len(user.organizations_dict), 1)
        del expected[str(org2.pk)]
        self.assertEqual(user.organizations_dict, expected)

    def test_organizations_dict_cache(self):
        user = self._create_user(username='organizations_pk')
        org1 = self._create_org(name='org1')

        with self.assertNumQueries(1):
            list(user.organizations_dict)

        with self.assertNumQueries(0):
            list(user.organizations_dict)

        OrganizationUser.objects.create(user=user, organization=org1)

        # cache is automatically updated
        with self.assertNumQueries(0):
            list(user.organizations_dict)

    def test_is_member(self):
        user = self._create_user(username='organizations_pk')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self.assertFalse(user.is_member(org1))
        self.assertFalse(user.is_member(org2))
        OrganizationUser.objects.create(user=user, organization=org1)
        self.assertTrue(user.is_member(org1))
        self.assertFalse(user.is_member(org2))

    def test_is_manager(self):
        user = self._create_user(username='organizations_pk')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self.assertFalse(user.is_manager(org1))
        self.assertFalse(user.is_manager(org2))
        ou = OrganizationUser.objects.create(user=user, organization=org1)
        self.assertFalse(user.is_manager(org1))
        self.assertFalse(user.is_manager(org2))
        ou.is_admin = True
        ou.save()
        self.assertTrue(user.is_manager(org1))
        self.assertFalse(user.is_manager(org2))

    def test_is_owner(self):
        user = self._create_user(username='organizations_pk')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self.assertFalse(user.is_owner(org1))
        self.assertFalse(user.is_owner(org2))
        OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
        self.assertTrue(user.is_owner(org1))
        self.assertFalse(user.is_owner(org2))

    def test_organization_repr(self):
        org = self._create_org(name='org1', is_active=False)
        self.assertIn('disabled', str(org))

    def test_organization_owner_bad_organization(self):
        user = self._create_user(username='user1', email='abc@example.com')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        org_user = self._create_org_user(organization=org1, user=user)
        org_owner = self._create_org_owner()
        org_owner.organization = org2
        org_owner.organization_user = org_user
        with self.assertRaises(ValidationError):
            org_owner.full_clean()

    def test_create_users_without_email(self):
        options = {
            'username': 'testuser',
            'password': 'test1',
        }
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)
        options['username'] = 'testuser2'
        u = self.user_model(**options)
        u.full_clean()
        u.save()
        self.assertIsNone(u.email)
        self.assertEqual(User.objects.filter(email=None).count(), 2)

    def test_add_users_with_empty_phone_numbers(self):
        user1 = self.user_model(
            username='user1',
            email='email1@email.com',
            password='user1',
            phone_number='',
        )
        user2 = self.user_model(
            username='user2',
            email='email2@email.com',
            password='user2',
            phone_number='',
        )
        user1.full_clean()
        user2.full_clean()
        user1.save()
        user2.save()
        self.assertIsNone(user1.phone_number)
        self.assertIsNone(user2.phone_number)
        self.assertEqual(self.user_model.objects.filter(phone_number=None).count(), 2)

    def test_cache_user_permission(self):
        user = self.user_model(
            username='user', email='email1@email.com', password='user1', is_staff=True
        )
        user.full_clean()
        user.save()
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)

        with self.subTest('Test cached permissions'):
            with self.assertNumQueries(0):
                user.permissions
            self.assertEqual(user.get_all_permissions(), user.permissions)

        with self.subTest('Test group permissions changed'):
            self.assertIn('account.view_emailaddress', user.permissions)
            permission = Permission.objects.get(codename='view_emailaddress')
            g = group.first()
            g.permissions.remove(permission.pk)
            g.refresh_from_db()
            self.assertNotIn('account.view_emailaddress', user.permissions)

        with self.subTest('Test group changed'):
            user.groups.remove(group.first().pk)
            user.groups.set(Group.objects.filter(name='Operator'))
            with self.assertNumQueries(0):
                self.assertEqual(user.get_all_permissions(), user.permissions)

        with self.subTest('Test user permission changed'):
            permission = Permission.objects.filter(codename='add_organization')
            user.user_permissions.add(*permission)
            with self.assertNumQueries(0):
                self.assertEqual(user.get_all_permissions(), user.permissions)

    def test_operator_has_permission(self):
        app_label = 'account'
        user = self.user_model(
            username='user', email='email1@email.com', password='user1', is_staff=True
        )
        user.full_clean()
        user.save()
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)
        self.assertFalse(user.has_permission(f'{app_label}.view_wrong'))
        self.assertTrue(user.has_permission(f'{app_label}.view_emailaddress'))

    def test_superuser_has_permission(self):
        user = self.user_model(
            username='superuser',
            email='email@email.com',
            password='test',
            is_staff=True,
            is_superuser=True,
        )
        user.full_clean()
        user.save()
        self.assertTrue(user.has_permission('not_found.not_found'))
