from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import resolve, reverse
from openwisp_users.tests import TestOrganizationMixin

from .models import Config, Template


class TestIntegration(TestOrganizationMixin, TestCase):
    def test_derived_model_config(self):
        self.assertEqual(Template.objects.count(), 0)
        t = Template(name='test')
        t.full_clean()
        t.save()
        self.assertEqual(Template.objects.count(), 1)

    def test_derived_model_template(self):
        c = Config(name='test')
        with self.assertRaises(ValidationError):
            c.full_clean()

    def test_validate_org_relation_pk_comparison_bug(self):
        self.assertEqual(Config.objects.count(), 0)
        org = self._create_org()
        t = Template.objects.create(name='test', organization=org)
        c = Config(name='test', template=t, organization_id=str(org.pk))
        c.full_clean()
        c.save()
        self.assertEqual(Config.objects.count(), 1)

    def test_resolve_account_URLs(self):
        resolver = resolve('/accounts/login/')
        self.assertEqual(resolver.view_name, 'account_login')
        resolver = resolve('/accounts/signup/')
        self.assertEqual(resolver.view_name, 'account_signup')
        resolver = resolve('/accounts/logout/')
        self.assertEqual(resolver.view_name, 'account_logout')
        resolver = resolve('/accounts/password/reset/')
        self.assertEqual(resolver.view_name, 'account_reset_password')

    def test_account_email_verification_sent(self):
        r = self.client.get(reverse('account_email_verification_sent'))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Change E-mail</a></li>')
        self.assertNotContains(r, 'Sign Up</a></li>')

    def test_account_confirm_email(self):
        r = self.client.get(reverse('account_confirm_email', args=['abc123']))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Change E-mail</a></li>')
        self.assertNotContains(r, 'Sign Up</a></li>')

    def test_account_reset_password(self):
        r = self.client.get(reverse('account_reset_password'))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Change E-mail</a></li>')
        self.assertNotContains(r, 'Sign Up</a></li>')
