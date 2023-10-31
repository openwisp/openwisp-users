from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.template import TemplateDoesNotExist
from django.test import TestCase
from django.urls import reverse

from ..accounts.adapter import EmailAdapter, authenticate
from .utils import TestOrganizationMixin

User = get_user_model()


class TestEmailAdapter(TestOrganizationMixin, TestCase):
    def test_template_not_present(self):
        email = "test@tester.com"
        template_prefix = "some_random_name"

        with self.assertRaises(TemplateDoesNotExist):
            EmailAdapter.send_mail(self, template_prefix, email, {})

    @mock.patch('openwisp_users.accounts.adapter.send_email')
    def test_assertion_not_raised_when_html_template_missing(self, mail_func):
        self._create_user()
        queryset = User.objects.filter(username='tester')
        self.assertEqual(queryset.count(), 1)
        params = {'email': 'test@tester.com'}
        self.client.post(reverse('account_reset_password'), params, follow=True)
        send_mail_calls = mail_func.call_args_list
        send_mail_arguments = send_mail_calls[0][0]
        self.assertEqual(send_mail_arguments[0], '[example.com] Password Reset E-mail')
        self.assertEqual(send_mail_arguments[2], '')

    def test_password_reset_email_sent(self):
        self._create_user()
        queryset = User.objects.filter(username='tester')
        self.assertEqual(queryset.count(), 1)
        params = {'email': 'test@tester.com'}
        self.client.post(reverse('account_reset_password'), params, follow=True)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertFalse(email.alternatives)
        self.assertIn('Password Reset E-mail', email.subject)
        self.assertIn('Click the link below to reset your password', email.body)

    @mock.patch('openwisp_users.accounts.adapter.django_authenticate')
    def test_authenticate_method(self, mocked_django_authenticate):
        authenticate_kwargs = dict(phone_number='987643210', otp='123456')

        from inspect import Signature

        def patched_bind(self, *args, **kwargs):
            if kwargs == authenticate_kwargs:
                raise TypeError
            return self._original_bind(*args, **kwargs)

        Signature._original_bind = Signature.bind
        Signature.bind = patched_bind

        authenticate(**authenticate_kwargs)
        mocked_django_authenticate.assert_called_once_with(None, **authenticate_kwargs)

        Signature.bind = Signature._original_bind
        del Signature._original_bind
