from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .utils import TestOrganizationMixin

User = get_user_model()


class TestEmailAdapter(TestOrganizationMixin, TestCase):
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
