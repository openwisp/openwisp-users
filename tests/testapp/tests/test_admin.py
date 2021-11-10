import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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

    def test_organization_default_label(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        with self.subTest('Test required organization label'):
            r = self.client.get(reverse('admin:testapp_book_add'))
            self.assertContains(r, '<option value="" selected>---------</option>')

        with self.subTest('Test optional organization label for superuser'):
            r = self.client.get(reverse('admin:testapp_template_add'))
            self.assertContains(
                r,
                '<option value="" selected>Shared systemwide (no organization)',
            )

        with self.subTest('Test optional organization label for non-superuser'):
            operator = self._create_operator()
            template_permissions = Permission.objects.filter(codename='add_template')
            operator.user_permissions.add(*template_permissions)
            self.client.force_login(operator)
            r = self.client.get(reverse('admin:testapp_template_add'))
            self.assertNotContains(
                r,
                'Shared systemwide (no organization)',
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
