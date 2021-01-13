from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from openwisp_users.api.throttling import AuthRateThrottle

from ..models import Book, Shelf
from .mixins import TestMultitenancyMixin

OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
User = get_user_model()


class TestFilterClasses(TestMultitenancyMixin, TestCase):
    def setUp(self):
        AuthRateThrottle.rate = 0
        self.shelf_model = Shelf
        self.book_model = Book
        self._create_org(name='org_a', slug='org_a')
        self._create_org(name='org_b', slug='org_b')
        self.shelf_a = self._create_shelf(
            name='test-shelf-a', organization=self._get_org('org_a')
        )
        self.shelf_b = self._create_shelf(
            name='test-shelf-b', organization=self._get_org('org_b')
        )
        self.book1 = self._create_book(
            name='book1', organization=self._get_org('org_a'), shelf=self.shelf_a
        )
        self.book2 = self._create_book(
            name='book2', organization=self._get_org('org_a'), shelf=self.shelf_b
        )

    def test_browsable_api_filter_manager(self):
        operator = self._get_operator()
        # First user is automatically owner, so created dummy
        # user to keep operator as manager only.
        self._create_org_user(
            user=self._get_user(), is_admin=True, organization=self._get_org('org_a')
        )
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
            '?format=api',
            **auth,
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertNotContains(response, 'org_b</option>')
        self.assertNotContains(response, 'test-shelf-b</option>')

    def test_browsable_api_filter_owner(self):
        operator = self._get_operator()
        # First user is automatically owner
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
            '?format=api',
            **auth,
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertNotContains(response, 'org_b</option>')
        self.assertNotContains(response, 'test-shelf-b</option>')

    def test_browsable_api_filter_superuser(self):
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
            '?format=api',
            **auth,
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertContains(response, 'org_b</option>')
        self.assertContains(response, 'test-shelf-b</option>')

    def test_filter_by_parent_membership(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(
            reverse("test_books_list_member_view", args=(self.shelf_a.id,)), **auth,
        )
        self.assertEqual(response.data[0]['id'], str(self.book1.id))
        self.assertNotContains(response, str(self.book2.id))

    def test_filter_by_parent_managed(self):
        operator = self._get_operator()
        self._create_org_user(
            user=self._get_user(), is_admin=True, organization=self._get_org('org_a')
        )
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            reverse("test_books_list_manager_view", args=(self.shelf_a.id,)), **auth,
        )
        self.assertEqual(response.data[0]['id'], str(self.book1.id))
        self.assertNotContains(response, str(self.book2.id))

    def test_filter_by_parent_owned(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            reverse("test_books_list_owner_view", args=(self.shelf_a.id,)), **auth,
        )
        self.assertEqual(response.data[0]['id'], str(self.book1.id))
        self.assertNotContains(response, str(self.book2.id))

    def test_filter_by_org_membership(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse("test_shelf_list_member_view"), **auth,)
        self.assertEqual(response.data[0]['id'], str(self.shelf_a.id))
        self.assertNotContains(response, str(self.shelf_b.id))

    def test_filter_by_org_managed(self):
        operator = self._get_operator()
        self._create_org_user(
            user=self._get_user(), is_admin=True, organization=self._get_org('org_a')
        )
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse("test_shelf_list_manager_view"), **auth,)
        self.assertEqual(response.data[0]['id'], str(self.shelf_a.id))
        self.assertNotContains(response, str(self.shelf_b.id))

    def test_filter_by_org_owned(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse("test_shelf_list_owner_view"), **auth,)
        self.assertEqual(response.data[0]['id'], str(self.shelf_a.id))
        self.assertNotContains(response, str(self.shelf_b.id))

    def test_browsable_api_filter_member(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        auth = dict(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(
            f'{reverse("test_books_list_member_view", args=(self.shelf_a.id,))}'
            '?format=api',
            **auth,
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertNotContains(response, 'org_b</option>')
        self.assertNotContains(response, 'test-shelf-b</option>')
