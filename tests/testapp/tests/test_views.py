from unittest.mock import patch

from django.contrib.admin import site
from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from openwisp_users.tests.utils import TestMultitenantAdminMixin
from openwisp_utils.tests import capture_stderr

Organization = load_model('openwisp_users', 'Organization')
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


class TestAutocompleteJsonView(TestMultitenantAdminMixin, TestCase):
    def test_autocomplete_view_organization_filter(self):
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        self._get_admin()
        self._create_administrator(organizations=[org1])
        self._test_multitenant_admin(
            url=self._get_autocomplete_view_path('testapp', 'book', 'organization'),
            visible=[org1.name],
            hidden=[org2.name],
            administrator=True,
        )

    @capture_stderr()
    def test_autocomplete_view_blank_option(self):
        admin = self._get_admin()
        self.client.force_login(admin)
        path = reverse('admin:ow-auto-filter')
        with self.subTest('Test for Book.shelf filter'):
            response = self.client.get(
                path,
                data={
                    'app_label': 'testapp',
                    'model_name': 'book',
                    'field_name': 'shelf',
                },
            )
            for option in response.json()['results']:
                if option['id'] == 'null':
                    self.assertEqual(option['text'], '-')
                    break
            else:
                self.fail('Null option not found in response')

        with self.subTest('Test for Shelf.organization filter'):
            response = self.client.get(
                path,
                data={
                    'app_label': 'testapp',
                    'model_name': 'shelf',
                    'field_name': 'organization',
                },
            )
            for option in response.json()['results']:
                if option['id'] == 'null':
                    self.assertEqual(
                        option['text'], 'Shared systemwide (no organization)'
                    )
                    break
            else:
                self.fail('Null option not found in response')

    def test_autocomplete_view_for_inline_admin(self):
        admin = self._get_admin()
        self.client.force_login(admin)
        path = reverse('admin:ow-auto-filter')
        with patch.object(site, '_registry', site._registry) as mocked_registry:
            mocked_registry.pop(OrganizationUser)
            response = self.client.get(
                path,
                data={
                    'app_label': OrganizationUser._meta.app_label,
                    'model_name': OrganizationUser._meta.model_name,
                    'field_name': 'organization',
                },
            )
        self.assertEqual(len(response.json()['results']), Organization.objects.count())
