import os
import smtplib
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from openwisp_users.models import Organization, OrganizationUser, User

from .utils import TestMultitenantAdminMixin, TestOrganizationMixin

devnull = open(os.devnull, 'w')


class TestUsersAdmin(TestOrganizationMixin, TestCase):
    """ test admin site """

    add_user_inline_params = {
        'emailaddress_set-TOTAL_FORMS': 0,
        'emailaddress_set-INITIAL_FORMS': 0,
        'emailaddress_set-MIN_NUM_FORMS': 0,
        'emailaddress_set-MAX_NUM_FORMS': 0,
        'openwisp_users_organizationuser-TOTAL_FORMS': 0,
        'openwisp_users_organizationuser-INITIAL_FORMS': 0,
        'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
        'openwisp_users_organizationuser-MAX_NUM_FORMS': 0,
    }

    def test_admin_add_user_auto_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
        )
        params.update(self.add_user_inline_params)
        self.client.post(reverse('admin:openwisp_users_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 1)
        user = queryset.first()
        self.assertEqual(user.emailaddress_set.count(), 1)
        emailaddress = user.emailaddress_set.first()
        self.assertEqual(emailaddress.email, 'test@testadd.com')
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_add_user_empty_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testadd', email='', password1='tester', password2='tester'
        )
        params.update(self.add_user_inline_params)
        response = self.client.post(reverse('admin:openwisp_users_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 0)
        self.assertContains(response, 'errors field-email')
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_change_user_auto_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        user = self._create_user(username='changemailtest')
        params = user.__dict__
        params['email'] = 'new@mail.com'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        # inline emails
        params.update(
            {
                'emailaddress_set-TOTAL_FORMS': 1,
                'emailaddress_set-INITIAL_FORMS': 1,
                'emailaddress_set-MIN_NUM_FORMS': 0,
                'emailaddress_set-MAX_NUM_FORMS': 0,
                'emailaddress_set-0-verified': True,
                'emailaddress_set-0-primary': True,
                'emailaddress_set-0-id': user.emailaddress_set.first().id,
                'emailaddress_set-0-user': user.id,
                'openwisp_users_organizationuser-TOTAL_FORMS': 0,
                'openwisp_users_organizationuser-INITIAL_FORMS': 0,
                'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
                'openwisp_users_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        response = self.client.post(
            reverse('admin:openwisp_users_user_change', args=[user.pk]),
            params,
            follow=True,
        )
        self.assertNotContains(response, 'error')
        user = User.objects.get(username='changemailtest')
        email_set = user.emailaddress_set
        self.assertEqual(email_set.count(), 2)
        self.assertEqual(email_set.filter(email='new@mail.com').count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_change_user_email_empty(self):
        admin = self._create_admin(email='')
        self.client.force_login(admin)
        params = dict(
            username='testchange',
            email='',
            first_name='',
            last_name='',
            bio='',
            url='',
            company='',
            location='',
        )
        params.update(
            {
                'emailaddress_set-TOTAL_FORMS': 0,
                'emailaddress_set-INITIAL_FORMS': 0,
                'emailaddress_set-MIN_NUM_FORMS': 0,
                'emailaddress_set-MAX_NUM_FORMS': 0,
                'openwisp_users_organizationuser-TOTAL_FORMS': 0,
                'openwisp_users_organizationuser-INITIAL_FORMS': 0,
                'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
                'openwisp_users_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        response = self.client.post(
            reverse('admin:openwisp_users_user_change', args=[admin.pk]), params
        )
        queryset = User.objects.filter(username='testchange')
        self.assertEqual(queryset.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, 'errors field-email')

    def test_organization_view_on_site(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._create_org()
        response = self.client.get(
            reverse('admin:openwisp_users_organization_change', args=[org.pk])
        )
        self.assertNotContains(response, 'viewsitelink')

    def test_organization_user_view_on_site(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._create_org()
        ou = org.add_user(admin)
        response = self.client.get(
            reverse('admin:openwisp_users_organizationuser_change', args=[ou.pk])
        )
        self.assertNotContains(response, 'viewsitelink')

    def test_admin_change_user_is_superuser_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[admin.pk])
        )
        html = '<input type="checkbox" name="is_superuser"'
        self.assertContains(response, html)

    def test_admin_change_user_is_superuser_absent(self):
        operator = self._create_operator()
        options = {
            'organization': self._get_org(),
            'is_admin': True,
            'user': self._get_operator(),
        }
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[operator.pk])
        )
        html = (
            '<input type="checkbox" name="is_superuser" checked id="id_is_superuser">'
        )
        self.assertNotContains(response, html)

    def test_admin_change_user_permissions_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[admin.pk])
        )
        html = '<select name="user_permissions"'
        self.assertContains(response, html)

    def test_admin_change_user_permissions_readonly(self):
        operator = self._create_operator()
        options = {
            'organization': self._get_org(),
            'is_admin': True,
            'user': self._get_operator(),
        }
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[operator.pk])
        )
        html = '<div class="readonly">openwisp_users'
        self.assertContains(response, html)

    def test_admin_changelist_user_superusers_hidden(self):
        self._create_admin()
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_changelist'))
        self.assertNotContains(response, 'admin</a>')

    def test_admin_changelist_operator_org_users_visible(self):
        # Check with operator in same organization and is_admin
        self._create_org_user()
        operator = self._create_operator()
        options = {'organization': self._get_org(), 'is_admin': True, 'user': operator}
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_changelist'))
        self.assertContains(response, 'tester</a>')
        self.assertContains(response, 'operator</a>')

    def test_operator_changelist_superuser_column_hidden(self):
        operator = self._create_operator()
        options = {'organization': self._get_org(), 'is_admin': True, 'user': operator}
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_changelist'))
        self.assertNotContains(response, 'Superuser status</a>')

    def test_operator_organization_member(self):
        org1 = self._create_org(name='operator-org1')
        org2 = self._create_org(name='operator-org2')
        operator = self._create_operator()
        options1 = {'organization': org1, 'is_admin': True, 'user': operator}
        options2 = {'organization': org2, 'is_admin': False, 'user': operator}
        self._create_org_user(**options1)
        self._create_org_user(**options2)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[operator.pk])
        )
        self.assertContains(response, 'selected>operator-org1</option>')
        self.assertContains(response, 'selected>operator-org2</option>')

    def test_operator_can_see_organization_add_user(self):
        org1 = self._create_org(name='operator-org1')
        org2 = self._create_org(name='operator-org2')
        operator = self._create_operator()
        org_permissions = Permission.objects.filter(
            codename__endswith='organization_user'
        )
        operator.user_permissions.add(*org_permissions)
        options1 = {'organization': org1, 'is_admin': True, 'user': operator}
        options2 = {'organization': org2, 'is_admin': False, 'user': operator}
        self._create_org_user(**options1)
        self._create_org_user(**options2)
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_add'))
        self.assertContains(response, 'operator-org1</option>')
        self.assertNotContains(response, 'operator-org2</option>')

    def test_operator_change_organization(self):
        org1 = self._create_org(name='test-org1')
        org2 = self._create_org(name='test-org2')
        default_org = Organization.objects.get(name='default')
        operator = self._create_operator()
        org_permissions = Permission.objects.filter(
            codename__endswith='change_organization'
        )
        operator.user_permissions.add(*org_permissions)
        options1 = {'organization': org1, 'is_admin': True, 'user': operator}
        options2 = {'organization': org2, 'is_admin': False, 'user': operator}
        self._create_org_user(**options1)
        self._create_org_user(**options2)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_organization_change', args=[org1.pk])
        )
        self.assertContains(
            response, '<input type="text" name="name" value="{0}"'.format(org1.name)
        )
        response = self.client.get(
            reverse('admin:openwisp_users_organization_change', args=[default_org.pk])
        )
        self.assertContains(
            response,
            '<input type="text" name="name" value="{0}"'.format(default_org.name),
        )
        response = self.client.get(
            reverse('admin:openwisp_users_organization_change', args=[org2.pk])
        )
        self.assertNotContains(
            response, '<input type="text" name="name" value="{0}"'.format(org2.name)
        )

    def test_operator_change_org_is_admin(self):
        org1 = self._create_org(name='test-org1')
        org2 = self._create_org(name='test-org2')
        operator = self._create_operator()
        org_permissions = Permission.objects.filter(
            codename__endswith='change_organization'
        )
        operator.user_permissions.add(*org_permissions)
        options1 = {'organization': org1, 'is_admin': True, 'user': operator}
        options2 = {'organization': org2, 'is_admin': False, 'user': operator}
        org_user1 = self._create_org_user(**options1)
        org_user2 = self._create_org_user(**options2)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_organizationuser_change', args=[org_user1.pk])
        )
        self.assertNotContains(
            response,
            '<input type="checkbox" name="is_admin" id="id_is_admin">'
            '<label class="vCheckboxLabel" for="id_is_admin">Is admin'
            '</label>',
        )
        response = self.client.get(
            reverse('admin:openwisp_users_organizationuser_change', args=[org_user2.pk])
        )
        self.assertNotContains(
            response,
            '<input type="checkbox" name="is_admin" id="id_is_admin">'
            '<label class="vCheckboxLabel" for="id_is_admin">Is admin'
            '</label>',
        )

    def test_admin_operator_delete_org_user(self):
        org1 = self._create_org(name='test-org1')
        org2 = self._create_org(name='test-org2')
        operator = self._create_operator()
        org_permissions = Permission.objects.filter(
            codename__endswith='organization_user'
        )
        operator.user_permissions.add(*org_permissions)
        options1 = {'organization': org1, 'is_admin': True, 'user': operator}
        options2 = {'organization': org2, 'is_admin': False, 'user': operator}
        org_user1 = self._create_org_user(**options1)
        org_user2 = self._create_org_user(**options2)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_organizationuser_change', args=[org_user1.pk])
        )
        self.assertContains(
            response,
            'class="deletelink-box">'
            '<a href="/admin/openwisp_users/organizationuser/{0}/delete/" '
            'class="deletelink">Delete'.format(org_user1.pk),
        )
        response = self.client.get(
            reverse('admin:openwisp_users_organizationuser_change', args=[org_user2.pk])
        )
        self.assertNotContains(response, 'delete')

    def test_admin_changelist_superuser_column_visible(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:openwisp_users_user_changelist'))
        self.assertContains(response, 'Superuser status</a>')

    def test_admin_operator_change_superuser_forbidden(self):
        admin = self._create_admin()
        operator = self._create_operator()
        options = {
            'organization': self._get_org(),
            'is_admin': True,
            'user': self._get_operator(),
        }
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[operator.pk])
        )
        self.assertEqual(response.status_code, 200)
        # operator trying to acess change form of superuser gets redirected
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[admin.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_new_user_email_exists(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
        )
        params.update(self.add_user_inline_params)
        self.client.post(reverse('admin:openwisp_users_user_add'), params)
        res = self.client.post(reverse('admin:openwisp_users_user_add'), params)
        self.assertContains(
            res, '<li>User with this Email address already exists.</li>'
        )

    def test_edit_user_email_exists(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        self._create_user()
        user = self._create_user(email='asd@asd.com', username='newTester')
        params = user.__dict__
        params['email'] = 'test@tester.com'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params.update(
            {
                'emailaddress_set-TOTAL_FORMS': 1,
                'emailaddress_set-INITIAL_FORMS': 1,
                'emailaddress_set-MIN_NUM_FORMS': 0,
                'emailaddress_set-MAX_NUM_FORMS': 0,
                'emailaddress_set-0-verified': True,
                'emailaddress_set-0-primary': True,
                'emailaddress_set-0-id': user.emailaddress_set.first().id,
                'emailaddress_set-0-user': user.id,
                'openwisp_users_organizationuser-TOTAL_FORMS': 0,
                'openwisp_users_organizationuser-INITIAL_FORMS': 0,
                'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
                'openwisp_users_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        res = self.client.post(
            reverse('admin:openwisp_users_user_change', args=[user.pk]),
            params,
            follow=True,
        )
        self.assertContains(
            res, '<li>User with this Email address already exists.</li>'
        )

    def test_admin_add_user_by_superuser(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        res = self.client.get(reverse('admin:openwisp_users_user_add'))
        self.assertContains(res, 'is_superuser')

    def test_admin_add_user_by_operator(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        res = self.client.get(reverse('admin:openwisp_users_user_add'))
        self.assertNotContains(res, 'is_superuser')

    def test_admin_add_user_org_required(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
            is_staff=True,
            is_superuser=False,
        )
        params.update(self.add_user_inline_params)
        params.update(
            {
                'openwisp_users_organizationuser-TOTAL_FORMS': 1,
                'openwisp_users_organizationuser-INITIAL_FORMS': 0,
                'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
                'openwisp_users_organizationuser-MAX_NUM_FORMS': 1,
            }
        )
        res = self.client.post(reverse('admin:openwisp_users_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 0)
        self.assertContains(res, 'errors field-organization')

    def test_admin_add_superuser_org_not_required(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
            is_staff=True,
            is_superuser=True,
        )
        params.update(self.add_user_inline_params)
        params.update(
            {
                'openwisp_users_organizationuser-TOTAL_FORMS': 1,
                'openwisp_users_organizationuser-INITIAL_FORMS': 0,
                'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
                'openwisp_users_organizationuser-MAX_NUM_FORMS': 1,
            }
        )
        res = self.client.post(
            reverse('admin:openwisp_users_user_add'), params, follow=True
        )
        self.assertNotContains(res, 'errors field-organization')
        self.assertNotContains(res, 'errors')
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 1)
        user = queryset.first()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_operator_change_user_permissions(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        admin = self._create_admin()
        response = self.client.get(
            reverse('admin:openwisp_users_user_change', args=[admin.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_user_add_user(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        # removing the "add_organizationuser" permission allows achieving more test coverage
        add_organizationuser = Permission.objects.get(
            codename__endswith='add_organizationuser'
        )
        operator.user_permissions.remove(add_organizationuser)
        response = self.client.get(reverse('admin:openwisp_users_user_add'))
        self.assertContains(response, '<input type="text" name="username"')

    def test_organization_owner(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        self._create_org_owner()
        response = self.client.get(
            reverse('admin:openwisp_users_organizationowner_changelist')
        )
        self.assertContains(response, 'tester')

    def test_organization_uuid_field(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:openwisp_users_organization_add'))
        html = '<input type="text" name="name" value="default"'
        self.assertNotContains(response, html)

    def test_action_active(self):
        user = User.objects.create(
            username='openwisp',
            password='test',
            email='openwisp@test.com',
            is_active=False,
        )
        path = reverse('admin:openwisp_users_user_changelist')
        self.client.force_login(self._get_admin())
        post_data = {
            '_selected_action': [user.pk],
            'action': 'make_active',
            'csrfmiddlewaretoken': 'test',
            'confirmation': 'Confirm',
        }
        response = self.client.post(path, post_data, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_action_inactive(self):
        user = User.objects.create(
            username='openwisp',
            password='test',
            email='openwisp@test.com',
            is_active=True,
        )
        path = reverse('admin:openwisp_users_user_changelist')
        self.client.force_login(self._get_admin())
        post_data = {
            '_selected_action': [user.pk],
            'action': 'make_inactive',
            'csrfmiddlewaretoken': 'test',
            'confirmation': 'Confirm',
        }
        response = self.client.post(path, post_data, follow=True)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(response.status_code, 200)

    def test_action_confirmation_page(self):
        user = User.objects.create(
            username='openwisp',
            password='test',
            email='openwisp@test.com',
            is_active=True,
        )
        path = reverse('admin:openwisp_users_user_changelist')
        self.client.force_login(self._get_admin())
        post_data = {
            '_selected_action': [user.pk],
            'action': 'make_active',
            'csrfmiddlewaretoken': 'test',
        }
        response = self.client.post(path, post_data, follow=True)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, 200)

    def test_superuser_delete_operator(self):
        user = self._create_operator()
        org = self._create_org()
        org_user = self._create_org_user(user=user, organization=org, is_admin=True)
        post_data = {
            '_selected_action': [user.pk],
            'action': 'delete_selected',
            'post': 'yes',
        }
        self.client.force_login(self._get_admin())
        path = reverse('admin:openwisp_users_user_changelist')
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=user.pk)
        org_user_qs = OrganizationUser.objects.filter(pk=org_user.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(user_qs.count(), 0)
        self.assertEqual(org_user_qs.count(), 0)

    @patch('sys.stdout', devnull)
    @patch('sys.stderr', devnull)
    def test_admin_add_user_with_invalid_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(
            username='testmail',
            email='test@invalid.com',
            password1='tester',
            password2='tester',
        )
        params.update(self.add_user_inline_params)
        with patch('allauth.account.models.EmailAddress.objects.add_email') as mocked:
            mocked.side_effect = smtplib.SMTPSenderRefused(
                501, '5.1.7 Bad sender address syntax', 'test_name@test_domain'
            )
            self.client.post(reverse('admin:openwisp_users_user_add'), params)
            mocked.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        devnull.close()


class TestBasicUsersIntegration(TestOrganizationMixin, TestCase):
    """
    tests basic integration with openwisp_users
    (designed to be inherited in other openwisp modules)
    """

    def _get_edit_form_inline_params(self, user, organization):
        organization_user = OrganizationUser.objects.get(
            user=user, organization=organization
        )
        return {
            # email address inline
            'emailaddress_set-TOTAL_FORMS': 1,
            'emailaddress_set-INITIAL_FORMS': 1,
            'emailaddress_set-MIN_NUM_FORMS': 0,
            'emailaddress_set-MAX_NUM_FORMS': 0,
            'emailaddress_set-0-verified': True,
            'emailaddress_set-0-primary': True,
            'emailaddress_set-0-id': user.emailaddress_set.first().id,
            'emailaddress_set-0-user': user.id,
            # organization user inline
            'openwisp_users_organizationuser-TOTAL_FORMS': 1,
            'openwisp_users_organizationuser-INITIAL_FORMS': 1,
            'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 1000,
            'openwisp_users_organizationuser-0-is_admin': False,
            'openwisp_users_organizationuser-0-organization': str(organization.pk),
            'openwisp_users_organizationuser-0-id': str(organization_user.pk),
            'openwisp_users_organizationuser-0-user': str(user.pk),
        }

    def test_change_user(self):
        admin = self._create_admin()
        user = self._create_user()
        org = Organization.objects.first()
        org.add_user(user)
        self.client.force_login(admin)
        params = user.__dict__
        params['bio'] = 'Test change'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params.update(self._get_edit_form_inline_params(user, org))
        response = self.client.post(
            reverse('admin:openwisp_users_user_change', args=[user.pk]),
            params,
            follow=True,
        )
        self.assertNotContains(response, 'error')
        user.refresh_from_db()
        self.assertEqual(user.bio, params['bio'])


class TestMultitenantAdmin(TestMultitenantAdminMixin, TestOrganizationMixin, TestCase):
    def _create_multitenancy_test_env(self):
        org1 = self._create_org(name='organization1')
        org2 = self._create_org(name='organization2')
        org3 = self._create_org(name='organization3')
        user1 = self._create_user(username='user1', email='user1j@something.com')
        user12 = self._create_user(username='user12', email='user12j@something.com')
        user2 = self._create_user(username='user2', email='user2j@something.com')
        user22 = self._create_user(username='user22', email='user22j@something.com')
        user23 = self._create_user(
            username='user23', email='user23j@something.com', is_superuser=True
        )
        user3 = self._create_user(username='user3', email='user3@something.com',)
        organization_user1 = self._create_org_user(organization=org1, user=user1)
        organization_user12 = self._create_org_user(organization=org1, user=user12)
        organization_user2 = self._create_org_user(organization=org2, user=user2)
        organization_user22 = self._create_org_user(organization=org2, user=user22)
        organization_owner1 = self._create_org_owner(
            organization_user=organization_user1, organization=org1
        )
        organization_owner2 = self._create_org_owner(
            organization_user=organization_user2, organization=org2
        )
        operator = self._create_operator()
        organization_user3 = self._create_org_user(
            organization=org3, user=operator, is_admin=True
        )
        organization_user31 = self._create_org_user(organization=org3, user=user3,)
        organization_user1o = self._create_org_user(organization=org1, user=operator,)
        data = dict(
            org1=org1,
            org2=org2,
            org3=org3,
            user1=user1,
            user2=user2,
            user12=user12,
            user22=user22,
            user23=user23,
            user3=user3,
            organization_user1=organization_user1,
            organization_user2=organization_user2,
            organization_user12=organization_user12,
            organization_user22=organization_user22,
            organization_user3=organization_user3,
            organization_user1o=organization_user1o,
            organization_user31=organization_user31,
            organization_owner1=organization_owner1,
            organization_owner2=organization_owner2,
            operator=operator,
        )
        return data

    def test_multitenancy_organization_user_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:openwisp_users_organizationuser_changelist'),
            hidden=[
                data['organization_user2'].user.username,
                data['organization_user22'].user.username,
            ],
            visible=[
                data['organization_user1'].user.username,
                data['organization_user12'].user.username,
                data['organization_user1o'].user.username,
                data['organization_user3'].user.username,
            ],
        )

    def test_multitenancy_organization_owner_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:openwisp_users_organizationowner_changelist'),
            hidden=[data['organization_owner2'].organization_user.user.username],
            visible=[data['organization_owner1'].organization_user.user.username],
        )

    def test_useradmin_specific_multitenancy_costraints(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse('admin:openwisp_users_user_changelist'),
            visible=[data['user3'], data['operator']],
            hidden=[data['user2'], data['user22'], data['user1'], data['user12']],
        )
