from django.core.exceptions import ValidationError
from django.test import TestCase
from openwisp_users.models import OrganizationUser, User

from .utils import TestOrganizationMixin


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
