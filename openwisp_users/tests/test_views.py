from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from .utils import TestMultitenantAdminMixin, TestOrganizationMixin

Organization = load_model('openwisp_users', 'Organization')


class TestAutocompleteJsonView(
    TestMultitenantAdminMixin, TestOrganizationMixin, TestCase
):
    def test_autocomplete_view_organization_filter(self):
        url = reverse('admin:ow-auto-filter')
        payload = {
            'app_label': 'testapp',
            'model_name': 'book',
            'field_name': 'organization',
        }
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')

        with self.subTest('Test with superuser'):
            admin = self._get_admin()
            self.client.force_login(admin)
            response = self.client.get(url, payload)
            for option in response.json()['results']:
                assert option['id'] in [
                    str(id) for id in Organization.objects.values_list('id', flat=True)
                ]

        with self.subTest('Test with organization user'):
            administrator = self._create_administrator(organizations=[org1])
            self.client.force_login(administrator)
            response = self.client.get(url, payload)
            for option in response.json()['results']:
                assert option['id'] in [str(org1.id)]
                assert option['id'] not in [str(org2.id)]
