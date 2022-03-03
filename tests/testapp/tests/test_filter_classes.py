from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.tests import AssertNumQueriesSubTestMixin
from swapper import load_model

from openwisp_users.api.throttling import AuthRateThrottle

from ..models import Book, Library, Shelf
from .mixins import TestMultitenancyMixin

OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
User = get_user_model()


class TestFilterClasses(AssertNumQueriesSubTestMixin, TestMultitenancyMixin, TestCase):
    def setUp(self):
        AuthRateThrottle.rate = 0
        self.shelf_model = Shelf
        self.book_model = Book
        self.library_model = Library
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
        url = f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
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
        url = f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertNotContains(response, 'org_b</option>')
        self.assertNotContains(response, 'test-shelf-b</option>')

    def test_browsable_api_filter_superuser(self):
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        url = f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertContains(response, 'org_b</option>')
        self.assertContains(response, 'test-shelf-b</option>')

    def test_filter_by_parent_membership(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        url = reverse('test_books_list_member_view', args=(self.shelf_a.id,))
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
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
        url = reverse('test_books_list_manager_view', args=(self.shelf_a.id,))
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.data[0]['id'], str(self.book1.id))
        self.assertNotContains(response, str(self.book2.id))

    def test_filter_by_parent_owned(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token()
        url = reverse('test_books_list_owner_view', args=(self.shelf_a.id,))
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.data[0]['id'], str(self.book1.id))
        self.assertNotContains(response, str(self.book2.id))

    def test_filter_by_org_membership(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        url = reverse('test_shelf_list_member_view')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
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
        url = reverse('test_shelf_list_manager_view')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.data[0]['id'], str(self.shelf_a.id))
        self.assertNotContains(response, str(self.shelf_b.id))

    def test_filter_by_org_managed_shared_objects(self):
        self._create_shelf(name='shared_shelf', organization=None)
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        url = f'{reverse("test_books_list_manager_view", args=(self.shelf_a.id,))}'
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertContains(response, 'shared_shelf</option>')

    def test_filter_by_org_owned(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token()
        url = reverse('test_shelf_list_owner_view')
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.data[0]['id'], str(self.shelf_a.id))
        self.assertNotContains(response, str(self.shelf_b.id))

    def test_browsable_api_filter_member(self):
        operator = self._get_operator()
        self._create_org_user(user=operator, organization=self._get_org('org_a'))
        token = self._obtain_auth_token(operator)
        url = f'{reverse("test_books_list_member_view", args=(self.shelf_a.id,))}'
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertContains(response, 'org_a</option>')
        self.assertContains(response, 'test-shelf-a</option>')
        self.assertNotContains(response, 'org_b</option>')
        self.assertNotContains(response, 'test-shelf-b</option>')

    def test_unauthorized_user(self):
        r = self.client.get(reverse("test_shelf_list_unauthorized_view"))
        self.assertEqual(r.status_code, 401)
        r = self.client.get(
            reverse('test_book_list_unauthorized_view', args=(self.shelf_a.id,))
        )
        self.assertEqual(r.status_code, 401)

    def test_presence_of_null_org_field(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        url = reverse('test_template_list')
        response = self.client.get(
            url, {'format': 'api'}, HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertNotContains(response, '--------</option>')

    def test_filter_by_org_managed_with_org_field(self):
        shared_shelf = self._create_shelf(name='shared_shelf', organization=None)
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        book_org1 = self._create_book(
            name='book_org1', organization=org1, shelf=shared_shelf
        )
        book_org2 = self._create_book(
            name='book_org2', organization=org2, shelf=shared_shelf
        )
        lib1 = self._create_library(name='lib1', book=book_org1)
        lib2 = self._create_library(name='lib2', book=book_org2)
        operator = self._get_operator()
        self._create_org_user(user=operator, is_admin=True, organization=org1)
        token = self._obtain_auth_token(operator)

        url = reverse('test_library_list')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        url = f'{reverse("test_library_detail", args=(lib1.id,))}'
        response = self.client.get(
            url, args=(lib1.id), HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 200)

        url = f'{reverse("test_library_detail", args=(lib2.id,))}'
        response = self.client.get(
            url, args=(lib1.id), HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, 404)

    def test_get_book_nested_shelf(self):
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        url = reverse('test_book_nested_shelf')
        with self.assertNumQueries(6):
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, 200)

    def test_post_book_nested_shelf(self):
        org1 = self._get_org('org_a')
        operator = self._get_operator()
        self._create_org_user(
            user=operator, is_admin=True, organization=self._get_org('org_a')
        )
        token = self._obtain_auth_token(operator)
        url = reverse('test_book_nested_shelf')
        data = {
            'shelf': {'name': 'test-shelf', 'organization': org1.pk},
            'name': 'test-book',
            'author': 'test-auther',
            'organization': org1.pk,
        }
        with self.assertNumQueries(12):
            response = self.client.post(
                url,
                data,
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {token}',
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Shelf.objects.count(), 3)
        self.assertEqual(Book.objects.count(), 3)

    def test_shelf_with_read_only_org_field(self):
        org1 = self._create_org(name='org1')
        operator = self._get_operator()
        self._create_org_user(user=operator, is_admin=True, organization=org1)
        self.client.force_login(operator)
        self._create_shelf(name='test-shelf-a', organization=org1)
        path = reverse('test_shelf_list_with_read_only_org')
        with self.assertNumQueries(4):
            response = self.client.get(path, {'format': 'api'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['organization'], org1.pk)
        self.assertNotContains(response, 'org1</option>')
