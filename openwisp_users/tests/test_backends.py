from uuid import UUID

from django.test import TestCase
from django.test.utils import override_settings

from openwisp_users.backends import UserAuthenticationBackend

from .utils import TestOrganizationMixin

auth_backend = UserAuthenticationBackend()


class TestBackends(TestOrganizationMixin, TestCase):
    def _test_user_auth_backend_helper(self, username, password, pk):
        self.client.login(username=username, password=password)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(
            UUID(self.client.session['_auth_user_id'], version=4), pk,
        )
        self.client.logout()
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_auth_backend(self):
        user = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        with self.subTest('Test login with username'):
            self._test_user_auth_backend_helper('tester', 'tester', user.pk)

        with self.subTest('Test login with email'):
            self._test_user_auth_backend_helper('tester@gmail.com', 'tester', user.pk)

        with self.subTest('Test login with phone_number'):
            self._test_user_auth_backend_helper('+237675579231', 'tester', user.pk)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_with_email_as_username_auth_backend(self):
        user = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        self._create_user(
            username='tester@gmail.com',
            email='tester1@gmail.com',
            phone_number='+237675579232',
            password='tester1',
        )
        self._test_user_auth_backend_helper(user.email, 'tester', user.pk)

    @override_settings(
        AUTHENTICATION_BACKENDS=('openwisp_users.backends.UserAuthenticationBackend',)
    )
    def test_user_with_phone_number_as_username_auth_backend(self):
        user = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        self._create_user(
            username='+237675579231',
            email='tester1@gmail.com',
            phone_number='+237675579232',
            password='tester1',
        )
        self._test_user_auth_backend_helper(user.phone_number, 'tester', user.pk)

    def test_auth_backend_get_user(self):
        user = self._create_user(
            username='tester',
            email='tester@gmail.com',
            phone_number='+237675579231',
            password='tester',
        )
        user1 = self._create_user(
            username='tester1',
            email='tester1@gmail.com',
            phone_number='+237675579232',
            password='tester1',
        )
        with self.subTest('get user with primary key'):
            self.assertEqual(auth_backend.get_user(user.pk), user)

        with self.subTest('get user with invalid identifier'):
            self.assertIsNone(auth_backend.get_user('invalid'))

        with self.subTest('get user with email'):
            user1.username = user.email
            user1.save()
            self.assertEqual(auth_backend.get_user(user.email), user)

        with self.subTest('get user with phone_number'):
            user1.username = user.phone_number
            user1.save()
            self.assertEqual(auth_backend.get_user(user.phone_number), user)

        with self.subTest('get user with username'):
            self.assertEqual(auth_backend.get_user(user.username), user)
