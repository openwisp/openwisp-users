from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from ..models import User
from .utils import TestOrganizationMixin


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
        'openwisp_users_organizationuser-MAX_NUM_FORMS': 0
    }

    def _create_operator(self, organizations=[]):
        operator = User.objects.create_user(username='operator',
                                            password='tester',
                                            email='operator@test.com',
                                            is_staff=True)
        operator.user_permissions.add(*Permission.objects.filter(codename__endswith='user'))
        return operator

    def test_admin_add_user_auto_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(username='testadd',
                      email='test@testadd.com',
                      password1='tester',
                      password2='tester')
        params.update(self.add_user_inline_params)
        self.client.post(reverse('admin:openwisp_users_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 1)
        user = queryset.first()
        self.assertEqual(user.emailaddress_set.count(), 1)
        emailaddress = user.emailaddress_set.first()
        self.assertEqual(emailaddress.email, 'test@testadd.com')
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_change_user_auto_email(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        user = self._create_user(username='changemailtest')
        params = user.__dict__
        params['email'] = 'new@mail.com'
        # inline emails
        params.update({
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
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 0
        })
        response = self.client.post(reverse('admin:openwisp_users_user_change', args=[user.pk]),
                                    params, follow=True)
        self.assertNotContains(response, 'error')
        user = User.objects.get(username='changemailtest')
        email_set = user.emailaddress_set
        self.assertEqual(email_set.count(), 2)
        self.assertEqual(email_set.filter(email='new@mail.com').count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_change_user_email_empty(self):
        admin = self._create_admin(email='')
        self.client.force_login(admin)
        params = dict(username='testchange',
                      email='',
                      first_name='',
                      last_name='',
                      bio='',
                      url='',
                      company='',
                      location='')
        params.update({
            'emailaddress_set-TOTAL_FORMS': 0,
            'emailaddress_set-INITIAL_FORMS': 0,
            'emailaddress_set-MIN_NUM_FORMS': 0,
            'emailaddress_set-MAX_NUM_FORMS': 0,
            'openwisp_users_organizationuser-TOTAL_FORMS': 0,
            'openwisp_users_organizationuser-INITIAL_FORMS': 0,
            'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 0
        })
        response = self.client.post(reverse('admin:openwisp_users_user_change', args=[admin.pk]), params)
        queryset = User.objects.filter(username='testchange')
        self.assertEqual(queryset.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, 'errors field-email')

    def test_organization_view_on_site(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._create_org()
        response = self.client.get(reverse('admin:openwisp_users_organization_change', args=[org.pk]))
        self.assertNotContains(response, 'viewsitelink')

    def test_organization_user_view_on_site(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        org = self._create_org()
        ou = org.add_user(admin)
        response = self.client.get(reverse('admin:openwisp_users_organizationuser_change', args=[ou.pk]))
        self.assertNotContains(response, 'viewsitelink')

    def test_admin_change_user_is_superuser_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[admin.pk]))
        html = '<input type="checkbox" name="is_superuser"'
        self.assertContains(response, html)

    def test_admin_change_user_is_superuser_readonly(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[operator.pk]))
        html = '<input type="checkbox" name="is_superuser" checked id="id_is_superuser">'
        self.assertNotContains(response, html)

    def test_admin_change_user_permissions_editable(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[admin.pk]))
        html = '<select name="user_permissions"'
        self.assertContains(response, html)

    def test_admin_change_user_permissions_readonly(self):
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[operator.pk]))
        html = '<div class="readonly">openwisp_users'
        self.assertContains(response, html)

    def test_admin_changelist_user_superusers_hidden(self):
        self._create_admin()
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_changelist'))
        self.assertNotContains(response, 'admin</a>')

    def test_admin_operator_change_superuser_forbidden(self):
        admin = self._create_admin()
        operator = self._create_operator()
        self.client.force_login(operator)
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[operator.pk]))
        self.assertEqual(response.status_code, 200)
        # operator trying to acess change form of superuser gets redirected
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[admin.pk]))
        self.assertEqual(response.status_code, 302)

    def test_new_user_email_exists(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(username='testadd',
                      email='test@testadd.com',
                      password1='tester',
                      password2='tester')
        params.update(self.add_user_inline_params)
        self.client.post(reverse('admin:openwisp_users_user_add'), params)
        res = self.client.post(reverse('admin:openwisp_users_user_add'), params)
        self.assertContains(res, '<li>User with this email already exists.</li>')

    def test_edit_user_email_exists(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        self._create_user()
        user = self._create_user(email='asd@asd.com', username='newTester')
        params = user.__dict__
        params['email'] = 'test@tester.com'
        params.update({
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
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 0
        })
        res = self.client.post(reverse('admin:openwisp_users_user_change', args=[user.pk]), params,
                               follow=True)
        self.assertContains(res, '<li>User with this email already exists.</li>')
        
    def test_operator_change_user_permissions(self):
        operator = self._create_operator()
        operator.is_staff = True
        # print(operator._meta.get_fields())
        operator.user_permissions.set(Permission.objects.all())
        self.client.force_login(operator)
        admin = self._create_admin()
        response = self.client.get(reverse('admin:openwisp_users_user_change', args=[admin.pk]))
        html = '<input type="checkbox" name="is_superuser"'
        self.assertNotContains(response, html)

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
        params = dict(username='testadd',
                      email='test@testadd.com',
                      password1='tester',
                      password2='tester',
                      is_staff=True,
                      is_superuser=False)
        params.update(self.add_user_inline_params)
        params.update({
            'openwisp_users_organizationuser-TOTAL_FORMS': 1,
            'openwisp_users_organizationuser-INITIAL_FORMS': 0,
            'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 1,
        })
        res = self.client.post(reverse('admin:openwisp_users_user_add'), params)
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 0)
        self.assertContains(res, 'errors field-organization')

    def test_admin_add_superuser_org_not_required(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        params = dict(username='testadd',
                      email='test@testadd.com',
                      password1='tester',
                      password2='tester',
                      is_staff=True,
                      is_superuser=True)
        params.update(self.add_user_inline_params)
        params.update({
            'openwisp_users_organizationuser-TOTAL_FORMS': 1,
            'openwisp_users_organizationuser-INITIAL_FORMS': 0,
            'openwisp_users_organizationuser-MIN_NUM_FORMS': 0,
            'openwisp_users_organizationuser-MAX_NUM_FORMS': 1,
        })
        res = self.client.post(reverse('admin:openwisp_users_user_add'), params,
                               follow=True)
        self.assertNotContains(res, 'errors field-organization')
        queryset = User.objects.filter(username='testadd')
        self.assertEqual(queryset.count(), 1)
        user = queryset.first()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
