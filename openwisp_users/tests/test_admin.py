import os
import smtplib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from swapper import load_model

from ..apps import logger as apps_logger
from .utils import (
    TestMultitenantAdminMixin,
    TestOrganizationMixin,
    TestUserAdditionalFieldsMixin,
)

Organization = load_model('openwisp_users', 'Organization')
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
User = get_user_model()
Group = load_model('openwisp_users', 'Group')

devnull = open(os.devnull, 'w')


class TestUsersAdmin(TestOrganizationMixin, TestUserAdditionalFieldsMixin, TestCase):
    """ test admin site """

    app_label = 'openwisp_users'

    def _get_org_edit_form_inline_params(self, user, organization):
        """
        This function is created to be overridden
        when the user extends openwisp-users
        and adds inline forms in the Organization model.
        """
        return dict()

    def _get_user_edit_form_inline_params(self, user, organization):
        """
        This function is created to be overridden
        when the user extends openwisp-users
        and adds inline forms in the User model
        """
        return dict()

    @property
    def add_user_inline_params(self):
        return {
            'emailaddress_set-TOTAL_FORMS': 0,
            'emailaddress_set-INITIAL_FORMS': 0,
            'emailaddress_set-MIN_NUM_FORMS': 0,
            'emailaddress_set-MAX_NUM_FORMS': 0,
            f'{self.app_label}_organizationuser-TOTAL_FORMS': 0,
            f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
            f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
            f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 0,
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
        params.update(self._additional_params_add())
        self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
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
        params.update(self._additional_params_add())
        response = self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 0)
        self.assertContains(response, 'errors field-email')
        self.assertEqual(len(mail.outbox), 0)

    def test_admin_change_user_auto_email(self):
        admin = self._create_admin()
        self._create_org_user(user=admin)
        self.client.force_login(admin)
        user = self._create_user(email='old@mail.com', username='changemailtest')
        params = user.__dict__
        params['email'] = 'new@mail.com'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params = self._additional_params_pop(params)
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
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 0,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        params.update(self._get_user_edit_form_inline_params(user, self._get_org()))
        response = self.client.post(
            reverse(f'admin:{self.app_label}_user_change', args=[user.pk]),
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
        self._create_org_user(user=admin)
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
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 0,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        params.update(self._get_user_edit_form_inline_params(admin, self._get_org()))
        response = self.client.post(
            reverse(f'admin:{self.app_label}_user_change', args=[admin.pk]), params
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
            reverse(f'admin:{self.app_label}_organization_change', args=[org.pk])
        )
        self.assertNotContains(response, 'viewsitelink')

    def test_organization_user_view_on_site(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._create_org()
        ou = self._create_org_user(organization=org, user=admin)
        response = self.client.get(
            reverse(f'admin:{self.app_label}_organizationuser_change', args=[ou.pk])
        )
        self.assertNotContains(response, 'viewsitelink')

    def test_admin_change_user_is_superuser_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(
            reverse(f'admin:{self.app_label}_user_change', args=[admin.pk])
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
            reverse(f'admin:{self.app_label}_user_change', args=[operator.pk])
        )
        html = (
            '<input type="checkbox" name="is_superuser" checked id="id_is_superuser">'
        )
        self.assertNotContains(response, html)

    def test_admin_change_user_permissions_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(
            reverse(f'admin:{self.app_label}_user_change', args=[admin.pk])
        )
        html = '<select name="user_permissions"'
        self.assertContains(response, html)

    def test_admin_change_non_superuser_readonly_fields(self):
        operator = self._create_operator()
        options = {
            'organization': self._get_org(),
            'is_admin': True,
            'user': self._get_operator(),
        }
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(
            reverse(f'admin:{self.app_label}_user_change', args=[operator.pk])
        )
        with self.subTest('User Permissions'):
            html = f'<div class="readonly">{self.app_label}'
            self.assertContains(response, html)
        with self.subTest('Organization User Inline'):
            html = 'class="readonly"><img src="/static/admin/img/icon'
            self.assertContains(response, html)

    def test_admin_changelist_user_superusers_hidden(self):
        self._create_admin()
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse(f'admin:{self.app_label}_user_changelist'))
        self.assertNotContains(response, 'admin</a>')

    def test_admin_changelist_operator_org_users_visible(self):
        # Check with operator in same organization and is_admin
        self._create_org_user()
        operator = self._create_operator()
        options = {'organization': self._get_org(), 'is_admin': True, 'user': operator}
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(reverse(f'admin:{self.app_label}_user_changelist'))
        self.assertContains(response, 'tester</a>')
        self.assertContains(response, 'operator</a>')

    def test_operator_changelist_superuser_column_hidden(self):
        operator = self._create_operator()
        options = {'organization': self._get_org(), 'is_admin': True, 'user': operator}
        self._create_org_user(**options)
        self.client.force_login(operator)
        response = self.client.get(reverse(f'admin:{self.app_label}_user_changelist'))
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
            reverse(f'admin:{self.app_label}_user_change', args=[operator.pk])
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
        response = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
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
            reverse(f'admin:{self.app_label}_organization_change', args=[org1.pk])
        )
        self.assertContains(
            response, '<input type="text" name="name" value="{0}"'.format(org1.name)
        )
        response = self.client.get(
            reverse(
                f'admin:{self.app_label}_organization_change', args=[default_org.pk]
            )
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse(f'admin:{self.app_label}_organization_change', args=[org2.pk])
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
            reverse(
                f'admin:{self.app_label}_organizationuser_change', args=[org_user1.pk]
            )
        )
        self.assertNotContains(
            response,
            '<input type="checkbox" name="is_admin" id="id_is_admin">'
            '<label class="vCheckboxLabel" for="id_is_admin">Is admin'
            '</label>',
        )
        response = self.client.get(
            reverse(
                f'admin:{self.app_label}_organizationuser_change', args=[org_user2.pk]
            )
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
            reverse(
                f'admin:{self.app_label}_organizationuser_change', args=[org_user1.pk]
            )
        )
        self.assertContains(
            response,
            'class="deletelink-box">'
            f'<a href="/admin/{self.app_label}/organizationuser/{org_user1.pk}'
            '/delete/" class="deletelink">Delete',
        )
        response = self.client.get(
            reverse(
                f'admin:{self.app_label}_organizationuser_change', args=[org_user2.pk]
            )
        )
        self.assertNotContains(response, 'delete')

    def test_admin_changelist_superuser_column_visible(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse(f'admin:{self.app_label}_user_changelist'))
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
            reverse(f'admin:{self.app_label}_user_change', args=[operator.pk])
        )
        self.assertEqual(response.status_code, 200)
        # operator trying to acess change form of superuser gets redirected
        response = self.client.get(
            reverse(f'admin:{self.app_label}_user_change', args=[admin.pk])
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
        params.update(self._additional_params_add())
        self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
        res = self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
        self.assertContains(
            res, '<li>User with this Email address already exists.</li>'
        )

    def test_edit_user_email_exists(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        self._get_org_user()
        user = self._create_user(email='asd@asd.com', username='newTester')
        self._create_org_user(user=user)
        params = user.__dict__
        params['email'] = 'test@tester.com'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params = self._additional_params_pop(params)
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
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 0,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 0,
            }
        )
        params.update(self._get_user_edit_form_inline_params(user, self._get_org()))
        res = self.client.post(
            reverse(f'admin:{self.app_label}_user_change', args=[user.pk]),
            params,
            follow=True,
        )
        self.assertContains(
            res, '<li>User with this Email address already exists.</li>'
        )

    def test_change_staff_without_group(self):
        self.client.force_login(self._get_admin())
        user = self._create_operator()
        self._create_org_user(user=user)
        params = user.__dict__
        params.pop('_password')
        params.pop('last_login')
        params.pop('phone_number')
        params.update(self.add_user_inline_params)
        params.update(self._additional_params_add())
        params.update(self._get_user_edit_form_inline_params(user, self._get_org()))
        path = reverse(f'admin:{self.app_label}_user_change', args=[user.pk])
        r = self.client.post(path, params, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r, 'A staff user must belong to a group, please select one.'
        )
        user.refresh_from_db()
        self.assertEqual(user.groups.count(), 0)

    def test_change_staff_with_group(self):
        self.client.force_login(self._get_admin())
        user = self._create_operator()
        org = self._get_org()
        self._create_org_user(organization=org, user=user)
        group = Group.objects.get(name='Administrator')
        params = user.__dict__
        params['groups'] = str(group.pk)
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params.update(self.add_user_inline_params)
        params.update(self._additional_params_add())
        params.update(self._get_user_edit_form_inline_params(user, org))
        path = reverse(f'admin:{self.app_label}_user_change', args=[user.pk])
        r = self.client.post(path, params, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'error')
        user.refresh_from_db()
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.get(name='Administrator').pk, group.pk)

    def test_staff_cannot_edit_org_owner(self):
        user1 = self._create_user(
            username="user1", email="email1@mail.com", is_staff=True
        )
        user2 = self._create_user(
            username="user2", email="email2@mail.com", is_staff=True
        )
        org = self._get_org()
        org_user2 = self._create_org_user(user=user2, organization=org, is_admin=True)
        self._create_org_user(user=user1, organization=org, is_admin=True)
        group = Group.objects.filter(name='Administrator')
        user1.groups.set(group)
        user2.groups.set(group)
        self.client.force_login(user1)
        path = reverse(f'admin:{self.app_label}_user_change', args=[user2.pk])
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'class="readonly">{user2.username}')
        message = (
            "You do not have permission to edit or delete "
            "this user because they are owner of an organization."
        )
        self.assertContains(r, message)

        org_owner = OrganizationOwner.objects.get(organization_user=org_user2)
        org_owner.delete()
        path = reverse(f'admin:{self.app_label}_user_change', args=[user2.pk])
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, f'class="readonly">{user2.username}')

    def _test_change(self, options):
        user1 = None
        user2 = None
        group = Group.objects.get(name='Administrator')
        org = self._get_org()
        for key, user in options.items():
            u = self._create_user(**user.get('fields'))
            self._create_org_user(user=u, organization=org, is_admin=True)
            u.groups.add(group)
            if user1:
                user2 = u
                continue
            user1 = u
        if user1 and not user2:
            user2 = user1
        self.client.force_login(user1)
        params = user2.__dict__
        params['username'] = 'newuser1'
        params['groups'] = str(group.pk)
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params.update(self.add_user_inline_params)
        params.update(self._additional_params_add())
        params.update(self._get_user_edit_form_inline_params(user2, org))
        path = reverse(f'admin:{self.app_label}_user_change', args=[user2.pk])
        r = self.client.post(path, params, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'error')
        user2.refresh_from_db()
        self.assertEqual(user2.username, 'newuser1')

    def test_staff_can_edit_staff(self):
        options = {
            'user1': {
                'fields': {
                    'username': 'user1',
                    'email': 'email1@mail.com',
                    'is_staff': True,
                },
                'is_owner': False,
            },
            'user2': {
                'fields': {
                    'username': 'user2',
                    'email': 'email2@mail.com',
                    'is_staff': True,
                },
                'is_owner': False,
            },
        }
        self._test_change(options)

    def test_org_owner_can_edit_staff(self):
        options = {
            'user1': {
                'fields': {
                    'username': 'user1',
                    'email': 'email1@mail.com',
                    'is_staff': True,
                },
                'is_owner': True,
            },
            'user2': {
                'fields': {
                    'username': 'user2',
                    'email': 'email2@mail.com',
                    'is_staff': True,
                },
                'is_owner': False,
            },
        }
        self._test_change(options)

    def test_org_owner_can_edit_org_owner(self):
        options = {
            'user1': {
                'fields': {
                    'username': 'user1',
                    'email': 'email1@mail.com',
                    'is_staff': True,
                },
                'is_owner': True,
            },
        }
        self._test_change(options)

    def test_staff_can_edit_itself(self):
        options = {
            'user1': {
                'fields': {
                    'username': 'user1',
                    'email': 'email1@mail.com',
                    'is_staff': True,
                },
                'is_owner': False,
            },
        }
        self._test_change(options)

    def test_admin_add_user_by_superuser(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        res = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
        self.assertContains(res, 'is_superuser')

    def test_admin_add_user_by_operator(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        res = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
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
        params.update(self._additional_params_add())
        params.update(
            {
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 1,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 1,
            }
        )
        res = self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 0)
        self.assertContains(res, 'errors field-organization')

    def test_admin_user_add_form(self):
        self.client.force_login(self._get_admin())
        r = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
        self.assertContains(r, 'first_name')
        self.assertContains(r, 'last_name')
        self.assertContains(r, 'phone_number')
        self.assertContains(r, 'groups')

    def test_add_staff_without_group(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._get_org()
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
            is_staff=True,
        )
        params.update(self.add_user_inline_params)
        params.update(self._additional_params_add())
        params.update(
            {
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 1,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 1,
                f'{self.app_label}_organizationuser-0-is_admin': 'on',
                f'{self.app_label}_organizationuser-0-organization': str(org.pk),
            }
        )
        res = self.client.post(
            reverse(f'admin:{self.app_label}_user_add'), params, follow=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertContains(
            res, 'A staff user must belong to a group, please select one.'
        )
        user = User.objects.filter(username='testadd')
        self.assertEqual(user.count(), 0)

    def test_add_staff_with_group(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        group = Group.objects.get(name='Administrator')
        org = self._get_org()
        params = dict(
            username='testadd',
            email='test@testadd.com',
            password1='tester',
            password2='tester',
            is_staff=True,
        )
        params.update(self.add_user_inline_params)
        params.update(self._additional_params_add())
        params.update(
            {
                'groups': str(group.pk),
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 1,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 1,
                f'{self.app_label}_organizationuser-0-is_admin': 'on',
                f'{self.app_label}_organizationuser-0-organization': str(org.pk),
            }
        )
        res = self.client.post(
            reverse(f'admin:{self.app_label}_user_add'), params, follow=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'error')
        user = User.objects.filter(username='testadd')
        self.assertEqual(user.count(), 1)

    def test_add_user_fieldsets(self):
        self.client.force_login(self._get_admin())
        r = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Permissions')
        self.assertContains(r, 'Personal Info')

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
        params.update(self._additional_params_add())
        params.update(
            {
                f'{self.app_label}_organizationuser-TOTAL_FORMS': 1,
                f'{self.app_label}_organizationuser-INITIAL_FORMS': 0,
                f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
                f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 1,
            }
        )
        res = self.client.post(
            reverse(f'admin:{self.app_label}_user_add'), params, follow=True
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
            reverse(f'admin:{self.app_label}_user_change', args=[admin.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_user_add_user(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        # removing the "add_organizationuser" permission allows
        # achieving more test coverage
        add_organizationuser = Permission.objects.get(
            codename__endswith='add_organizationuser'
        )
        operator.user_permissions.remove(add_organizationuser)
        response = self.client.get(reverse(f'admin:{self.app_label}_user_add'))
        self.assertContains(response, '<input type="text" name="username"')

    def test_organization_owner(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        self._create_org_owner()
        response = self.client.get(
            reverse(f'admin:{self.app_label}_organizationowner_changelist')
        )
        self.assertContains(response, 'tester')

    def test_first_org_manager_creates_org_owner(self):
        org = self._get_org()
        user = self._get_user()
        org_user = self._create_org_user(organization=org, user=user, is_admin=True)
        org_owner_qs = OrganizationOwner.objects.all()
        self.assertEqual(org_owner_qs.count(), 1)
        org_owner = org_owner_qs.first()
        self.assertEqual(org_owner.organization, org)
        self.assertEqual(org_owner.organization_user, org_user)

    def test_first_org_member_creates_no_org_owner(self):
        org = self._get_org()
        user = self._get_user()
        self._create_org_user(organization=org, user=user, is_admin=False)
        org_owner_qs = OrganizationOwner.objects.all()
        self.assertEqual(org_owner_qs.count(), 0)

    def test_second_orguser_creates_no_org_owner(self):
        org = self._get_org()
        user = self._get_user()
        org_user = self._create_org_user(organization=org, user=user, is_admin=True)
        user1 = self._create_user(username='user1', email='user1@gmail.com')
        self._create_org_user(organization=org, user=user1, is_admin=True)
        org_owner_qs = OrganizationOwner.objects.all()
        self.assertEqual(org_owner_qs.count(), 1)
        org_owner = org_owner_qs.first()
        self.assertEqual(org_owner.organization, org)
        self.assertEqual(org_owner.organization_user, org_user)

    def test_organzation_add_inline_owner_absent(self):
        self.client.force_login(self._get_admin())
        response = self.client.get(reverse(f'admin:{self.app_label}_organization_add'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Organization owners')

    def test_organzation_change_inline_owner_present(self):
        org = self._create_org()
        self.client.force_login(self._get_admin())
        response = self.client.get(
            reverse(f'admin:{self.app_label}_organization_change', args=[org.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Organization owners')

    @patch.object(
        OrganizationOwner, 'full_clean', side_effect=ValidationError('invalid')
    )
    @patch.object(apps_logger, 'exception')
    def test_invalid_org_owner(self, mocked_owner, logger_exception):
        org = self._create_org(name='invalid')
        user = self._create_user(username='invalid', email='invalid@email.com')
        org_user = self._create_org_user(organization=org, user=user, is_admin=True)
        mocked_owner.assert_called_once()
        logger_exception.assert_called_once()
        owner_qs = OrganizationOwner.objects.filter(organization_user=org_user)
        self.assertEqual(owner_qs.count(), 0)

    def test_organization_uuid_field(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse(f'admin:{self.app_label}_organization_add'))
        html = '<input type="text" name="name" value="default"'
        self.assertNotContains(response, html)

    def test_action_active(self):
        user = User.objects.create(
            username='openwisp',
            password='test',
            email='openwisp@test.com',
            is_active=False,
        )
        path = reverse(f'admin:{self.app_label}_user_changelist')
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
        path = reverse(f'admin:{self.app_label}_user_changelist')
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
        path = reverse(f'admin:{self.app_label}_user_changelist')
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
        path = reverse(f'admin:{self.app_label}_user_changelist')
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=user.pk)
        org_user_qs = OrganizationUser.objects.filter(pk=org_user.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(user_qs.count(), 0)
        self.assertEqual(org_user_qs.count(), 0)

    def test_staff_delete_staff(self):
        org = self._create_org()
        staff = self._create_user(
            username='staff', is_staff=True, email='staff@gmail.com'
        )
        group = Group.objects.filter(name='Administrator')
        staff.groups.set(group)
        self._create_org_user(organization=org, user=staff, is_admin=True)
        op = self._create_operator()
        op.groups.set(group)
        self._create_org_user(organization=org, user=op, is_admin=True)
        post_data = {
            '_selected_action': [op.pk],
            'action': 'delete_selected_overridden',
            'post': 'yes',
        }
        path = reverse(f'admin:{self.app_label}_user_changelist')
        self.client.force_login(staff)
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=op.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(user_qs.count(), 0)
        self.assertContains(r, 'Successfully deleted 1 user')

    def test_superuser_delete_staff(self):
        org = self._create_org()
        group = Group.objects.filter(name='Administrator')
        op = self._create_operator()
        op.groups.set(group)
        self._create_org_user(organization=org, user=op, is_admin=True)
        post_data = {
            '_selected_action': [op.pk],
            'action': 'delete_selected_overridden',
            'post': 'yes',
        }
        path = reverse(f'admin:{self.app_label}_user_changelist')
        self.client.force_login(self._get_admin())
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=op.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(user_qs.count(), 0)
        self.assertContains(r, 'Successfully deleted 1 user')

    def test_staff_delete_org_owner(self):
        org = self._create_org()
        staff = self._create_user(
            username='staff', is_staff=True, email='staff@gmail.com'
        )
        group = Group.objects.filter(name='Administrator')
        staff.groups.set(group)
        op = self._create_operator()
        op.groups.set(group)
        self._create_org_user(organization=org, user=op, is_admin=True)
        self._create_org_user(organization=org, user=staff, is_admin=True)
        path = reverse(f'admin:{self.app_label}_user_changelist')
        post_data = {
            'action': 'delete_selected_overridden',
            '_selected_action': [op.pk],
            'post': 'yes',
        }
        self.client.force_login(staff)
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=op.pk)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f"delete 1 organization owner: {op.username}")
        self.assertEqual(user_qs.count(), 1)

    def test_superuser_delete_org_owner(self):
        org = self._create_org()
        group = Group.objects.filter(name='Administrator')
        op = self._create_operator()
        op.groups.set(group)
        self._create_org_user(organization=org, user=op, is_admin=True)
        path = reverse(f'admin:{self.app_label}_user_changelist')
        post_data = {
            'action': 'delete_selected_overridden',
            '_selected_action': [op.pk],
            'post': 'yes',
        }
        self.client.force_login(self._get_admin())
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.filter(pk=op.pk)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Successfully deleted 1 user')
        self.assertEqual(user_qs.count(), 0)

    def test_staff_bulk_delete(self):
        org = self._create_org()
        group = Group.objects.filter(name='Administrator')
        staff = self._create_user(
            username='staff', is_staff=True, email='staff@gmail.com'
        )
        staff.groups.set(group)
        op1 = self._create_user(username='op1', is_staff=True, email='op1@gmail.com')
        op2 = self._create_user(username='op2', is_staff=True, email='op2@gmail.com')
        op1.groups.set(group)
        op2.groups.set(group)
        self._create_org_user(organization=org, user=op1, is_admin=True)
        self._create_org_user(organization=org, user=op2, is_admin=True)
        self._create_org_user(organization=org, user=staff, is_admin=True)
        post_data = {
            'action': 'delete_selected_overridden',
            '_selected_action': [op1.pk, op2.pk],
        }
        path = reverse(f'admin:{self.app_label}_user_changelist')
        self.client.force_login(staff)
        r = self.client.post(path, post_data, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f"delete 1 organization owner: {op1.username}")
        post_data.update({'post': 'yes'})
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.all()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Successfully deleted 1 user')
        self.assertEqual(user_qs.count(), 3)
        self.assertEqual(user_qs.filter(pk=op2.pk).count(), 0)
        self.assertEqual(user_qs.filter(pk=op1.pk).count(), 1)

    def test_superuser_bulk_delete(self):
        org = self._create_org()
        group = Group.objects.filter(name='Administrator')
        op1 = self._create_user(username='op1', is_staff=True, email='op1@gmail.com')
        op2 = self._create_user(username='op2', is_staff=True, email='op2@gmail.com')
        op1.groups.set(group)
        op2.groups.set(group)
        self._create_org_user(organization=org, user=op1, is_admin=True)
        self._create_org_user(organization=org, user=op2, is_admin=True)
        post_data = {
            'action': 'delete_selected_overridden',
            '_selected_action': [op1.pk, op2.pk],
            'post': 'yes',
        }
        path = reverse(f'admin:{self.app_label}_user_changelist')
        self.client.force_login(self._get_admin())
        r = self.client.post(path, post_data, follow=True)
        user_qs = User.objects.all()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Successfully deleted 2 users')
        self.assertEqual(user_qs.count(), 2)

    def test_admin_user_has_change_org_perm(self):
        user = self._get_user()
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)
        self.assertIn(
            f'{self.app_label}.change_organization', user.get_all_permissions()
        )

    def test_can_change_org(self):
        org = self._get_org()
        user = self._create_user(
            username='change', password='change', email='email@email', is_staff=True
        )
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)
        org_user = self._create_org_user(user=user, organization=org, is_admin=True)
        path = reverse(f'admin:{self.app_label}_organization_change', args=[org.pk])

        with self.subTest('org owner can change org'):
            self.client.force_login(user)
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, f'<input type="text" name="name" value="{org.name}"')

        with self.subTest('managers can change org'):
            OrganizationOwner.objects.all().delete()
            self.client.force_login(user)
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, f'<input type="text" name="name" value="{org.name}"')

        with self.subTest('member can not edit org'):
            OrganizationOwner.objects.all().delete()
            org_user.is_admin = False
            org_user.save()
            self.client.force_login(user)
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, f'class="readonly">{org.name}')

    def test_only_superuser_has_add_delete_org_perm(self):
        user = self._create_user(
            username='change', password='change', email='email@email', is_staff=True
        )
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)
        org = self._get_org()
        add_params = {
            'name': 'new org',
            'slug': 'new',
            'owner-TOTAL_FORMS': '0',
            'owner-INITIAL_FORMS': '0',
            'owner-MIN_NUM_FORMS': '0',
            'owner-MAX_NUM_FORMS': '1',
        }
        delete_params = {
            'action': 'delete_selected',
            '_selected_action': [org.pk],
            'post': 'yes',
        }
        add_params.update(self._get_org_edit_form_inline_params(user, org))
        add_path = reverse(f'admin:{self.app_label}_organization_add')
        delete_path = reverse(f'admin:{self.app_label}_organization_changelist')

        with self.subTest('Administrators can not add org'):
            self.client.force_login(user)
            r = self.client.post(add_path, add_params, follow=True)
            self.assertEqual(r.status_code, 403)
            orgs = Organization.objects.filter(slug='new')
            self.assertEqual(orgs.count(), 0)

        with self.subTest('Administrators can not delete org'):
            self.client.force_login(user)
            r = self.client.post(delete_path, delete_params, follow=True)
            self.assertEqual(r.status_code, 200)
            orgs = Organization.objects.filter(pk=org.pk)
            self.assertEqual(orgs.count(), 1)

        with self.subTest('superuser can add org'):
            self.client.force_login(self._get_admin())
            r = self.client.post(add_path, add_params, follow=True)
            self.assertEqual(r.status_code, 200)
            orgs = Organization.objects.get(name='new org')
            self.assertEqual(orgs.name, 'new org')

        with self.subTest('superuser can delete org'):
            self.client.force_login(self._get_admin())
            r = self.client.post(delete_path, delete_params, follow=True)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, 'Successfully deleted 1 organization')
            orgs = Organization.objects.filter(pk=org.pk)
            self.assertEqual(orgs.count(), 0)

    def test_can_change_inline_org_owner(self):
        user1 = self._create_user(
            username='user1', password='user1', email='email1@email', is_staff=True
        )
        user2 = self._create_user(
            username='user2', password='user2', email='email2@email', is_staff=True
        )
        group = Group.objects.filter(name='Administrator')
        user1.groups.set(group)
        user2.groups.set(group)
        org = self._get_org()
        org_user = self._create_org_user(user=user1, organization=org, is_admin=True)
        org_owner = OrganizationOwner.objects.get(organization_user=org_user)
        org_user2 = self._create_org_user(organization=org, user=user2, is_admin=True)
        params = {
            'name': org.name,
            'slug': org.slug,
            'owner-TOTAL_FORMS': '1',
            'owner-INITIAL_FORMS': '1',
            'owner-MIN_NUM_FORMS': '0',
            'owner-MAX_NUM_FORMS': '1',
            'owner-0-organization_user': f'{org_user.pk}',
            'owner-0-organization': f'{org.pk}',
            'owner-0-id': f'{org_owner.pk}',
        }
        path = reverse(f'admin:{self.app_label}_organization_change', args=[org.pk])
        with self.subTest('manager can not edit inline org owner'):
            self.client.force_login(user2)
            params.update(self._get_org_edit_form_inline_params(user2, org))
            params.update({'owner-0-organization_user': f'{org_user2.pk}'})
            r = self.client.post(path, params, follow=True)
            self.assertEqual(r.status_code, 200)
            org_owners = OrganizationOwner.objects.filter(organization_user=org_user2)
            self.assertEqual(org_owners.count(), 0)

        with self.subTest('owner can edit inline org owner'):
            self.client.force_login(user1)
            params.update(self._get_org_edit_form_inline_params(user1, org))
            params.update({'owner-0-organization_user': f'{org_user2.pk}'})
            r = self.client.post(path, params, follow=True)
            self.assertEqual(r.status_code, 200)
            org_owners = OrganizationOwner.objects.filter(organization_user=org_user2)
            self.assertEqual(org_owners.count(), 1)

        with self.subTest('superuser can edit inline org owner'):
            params.update(self._get_org_edit_form_inline_params(self._get_admin(), org))
            self.client.force_login(self._get_admin())
            user3 = self._create_user(
                username='user3', password='user3', email='email3@email', is_staff=True
            )
            user3.groups.set(group)
            org_user3 = self._create_org_user(
                organization=org, user=user3, is_admin=True
            )
            params.update({'owner-0-organization_user': f'{org_user3.pk}'})
            r = self.client.post(path, params, follow=True)
            self.assertEqual(r.status_code, 200)
            org_owners = OrganizationOwner.objects.filter(organization_user=org_user3)
            self.assertEqual(org_owners.count(), 1)

    def test_only_superuser_can_delete_inline_org_owner(self):
        org = self._get_org()
        user = self._create_user(
            username='change', password='change', email='email@email', is_staff=True
        )
        group = Group.objects.filter(name='Administrator')
        user.groups.set(group)
        self._create_org_user(organization=org, user=user, is_admin=True)
        path = reverse(f'admin:{self.app_label}_organization_change', args=[org.pk])

        with self.subTest('org owners can not delete inline org owner'):
            self.client.force_login(user)
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, '-DELETE">Delete')

        with self.subTest('managers can not delete inline org owner'):
            user1 = self._create_user(
                username='change1',
                password='change1',
                email='email1@email',
                is_staff=True,
            )
            user1.groups.set(group)
            self._create_org_user(organization=org, user=user1, is_admin=True)
            self.client.force_login(user1)
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, '-DELETE">Delete')

        with self.subTest('superuser can delete inline org owner'):
            self.client.force_login(self._get_admin())
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, '-DELETE">Delete')

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
        params.update(self._additional_params_add())
        with patch('allauth.account.models.EmailAddress.objects.add_email') as mocked:
            mocked.side_effect = smtplib.SMTPSenderRefused(
                501, '5.1.7 Bad sender address syntax', 'test_name@test_domain'
            )
            self.client.post(reverse(f'admin:{self.app_label}_user_add'), params)
            mocked.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        devnull.close()


class TestBasicUsersIntegration(
    TestOrganizationMixin, TestUserAdditionalFieldsMixin, TestCase
):
    """
    tests basic integration with openwisp_users
    (designed to be inherited in other openwisp modules)
    """

    app_label = 'openwisp_users'

    def _get_user_edit_form_inline_params(self, user, organization):
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
            'emailaddress_set-0-user': str(user.pk),
            # organization user inline
            f'{self.app_label}_organizationuser-TOTAL_FORMS': 1,
            f'{self.app_label}_organizationuser-INITIAL_FORMS': 1,
            f'{self.app_label}_organizationuser-MIN_NUM_FORMS': 0,
            f'{self.app_label}_organizationuser-MAX_NUM_FORMS': 1000,
            f'{self.app_label}_organizationuser-0-is_admin': False,
            f'{self.app_label}_organizationuser-0-organization': str(organization.pk),
            f'{self.app_label}_organizationuser-0-id': str(organization_user.pk),
            f'{self.app_label}_organizationuser-0-user': str(user.pk),
        }

    def test_change_user(self):
        admin = self._create_admin()
        user = self._create_user()
        org = Organization.objects.first()
        self._create_org_user(organization=org, user=user)
        self.client.force_login(admin)
        params = user.__dict__
        params['bio'] = 'Test change'
        params.pop('phone_number')
        params.pop('_password')
        params.pop('last_login')
        params = self._additional_params_pop(params)
        params.update(self._get_user_edit_form_inline_params(user, org))
        response = self.client.post(
            reverse(f'admin:{self.app_label}_user_change', args=[user.pk]),
            params,
            follow=True,
        )
        self.assertNotContains(response, 'error')
        user.refresh_from_db()
        self.assertEqual(user.bio, params['bio'])


class TestMultitenantAdmin(TestMultitenantAdminMixin, TestOrganizationMixin, TestCase):
    app_label = 'openwisp_users'

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
            url=reverse(f'admin:{self.app_label}_organizationuser_changelist'),
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
            url=reverse(f'admin:{self.app_label}_organizationowner_changelist'),
            hidden=[data['organization_owner2'].organization_user.user.username],
            visible=[data['organization_owner1'].organization_user.user.username],
        )

    def test_useradmin_specific_multitenancy_costraints(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse(f'admin:{self.app_label}_user_changelist'),
            visible=[data['user3'], data['operator']],
            hidden=[data['user2'], data['user22'], data['user1'], data['user12']],
        )
