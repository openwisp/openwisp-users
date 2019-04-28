from django.core.exceptions import ValidationError
from django.test import TestCase
from openwisp_users.models import OrganizationUser, User

from .utils import TestOrganizationMixin


class TestUsers(TestOrganizationMixin, TestCase):
    user_model = User

    def test_create_superuser_email(self):
        user = User.objects.create_superuser(username='tester',
                                             password='tester',
                                             email='test@superuser.com')
        self.assertEqual(user.emailaddress_set.count(), 1)
        self.assertEqual(user.emailaddress_set.first().email, 'test@superuser.com')

    def test_create_superuser_email_empty(self):
        user = User.objects.create_superuser(username='tester',
                                             password='tester',
                                             email='')
        self.assertEqual(user.emailaddress_set.count(), 0)

    def test_unique_email_validation(self):
        self._create_user(username='user1', email='same@gmail.com')
        options = {
            'username': 'user2',
            'email': 'same@gmail.com',
            'password': 'pass1'
        }
        u = self.user_model(**options)
        with self.assertRaises(ValidationError):
            u.full_clean()
            u.save()

    def test_create_user_without_email(self):
        options = {
            'username': 'testuser',
            'password': 'test1',
        }
        u = self.user_model(**options)
        u.full_clean()
        u.save()

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
