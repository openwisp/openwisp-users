import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from openwisp_users.tests.utils import TestOrganizationMixin

Organization = load_model('openwisp_users', 'Organization')
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
User = get_user_model()
Group = load_model('openwisp_users', 'Group')


class TestUsersAdmin(TestOrganizationMixin, TestCase):
    app_label = (
        'openwisp_users' if not os.environ.get('SAMPLE_APP', False) else 'sample_users'
    )

    def test_group_reversion(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        test_group = Group.objects.create()
        self.client.post(
            reverse(f'admin:{self.app_label}_group_change', args=(test_group.id,)),
            {'name': 'test_group_v1'},
            follow=True,
        )
        r = self.client.get(
            reverse(f'admin:{self.app_label}_group_revision', args=(test_group.id, 1))
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '<h1>Revert test_group_v1</h1>')

    def test_accounts_login(self):
        r = self.client.get(reverse('account_login'), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '<button class="primaryAction" type="submit">')
