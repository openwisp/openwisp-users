from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import resolve, reverse

from openwisp_users.tests.utils import TestOrganizationMixin

from ..models import Config, Template


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

    def test_validate_org_relation(self):
        c = Config(name='test')
        # simulates validating a relation instance attribute that has not been set yet
        self.assertEqual(c._validate_org_relation('not_set_yet'), None)

    def test_validate_org_relation_error(self):
        org = self._create_org()
        t = Template.objects.create(name='test', organization=org)
        c = Config(name='test', template=t)
        with self.assertRaises(ValidationError):
            c.full_clean()

    def test_validate_reverse_org_relation(self):
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        t = Template.objects.create(name='test-t', organization=org1)
        Config.objects.create(name='test-c1', template=t, organization=org1)
        with self.assertRaises(ValidationError):
            t.organization = org2
            t.full_clean()

    def test_validate_reverse_org_relation_return(self):
        t = Template(name='test-t')
        t.full_clean()
        org1 = self._create_org(name='org1')
        t = Template.objects.create(name='test-t', organization=org1)
        t.name = 'test-template'
        t.full_clean()

    def test_resolve_account_URLs(self):
        resolver = resolve('/accounts/login/')
        self.assertEqual(resolver.view_name, 'account_login')
        resolver = resolve('/accounts/signup/')
        self.assertEqual(resolver.view_name, 'account_signup')
        resolver = resolve('/accounts/logout/')
        self.assertEqual(resolver.view_name, 'account_logout')
        resolver = resolve('/accounts/password/reset/')
        self.assertEqual(resolver.view_name, 'account_reset_password')
        resolver = resolve('/accounts/password/change/')
        self.assertEqual(resolver.view_name, 'account_change_password')

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

    def test_account_change_password(self):
        response = self.client.get(reverse('account_change_password'))
        self.assertRedirects(
            response, '/accounts/login/?next=/accounts/password/change/'
        )
