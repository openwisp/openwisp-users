from datetime import date

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from swapper import load_model

from openwisp_users.multitenancy import SHARED_SYSTEMWIDE_LABEL

Organization = load_model("openwisp_users", "Organization")
OrganizationOwner = load_model("openwisp_users", "OrganizationOwner")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
Group = load_model("openwisp_users", "Group")
User = get_user_model()


class TestUserAdditionalFieldsMixin(object):
    _additional_user_fields = []

    def _additional_params_pop(self, params):
        fields = self._additional_user_fields
        for field in fields:
            params.pop(field[0])
        return params

    def _additional_params_add(self):
        params = dict()
        fields = self._additional_user_fields
        for field in fields:
            params.update({field[0]: field[1]})
        return params


class TestOrganizationMixin(object):
    def _create_user(self, **kwargs):
        opts = dict(
            username="tester",
            password="tester",
            first_name="Tester",
            last_name="Tester",
            email="test@tester.com",
            birth_date=date(1987, 3, 23),
        )
        opts.update(kwargs)
        user = User(**opts)
        user.full_clean()
        return User.objects.create_user(**opts)

    def _create_admin(self, **kwargs):
        """
        Creates a superuser.
        It could be renamed as _create_superuser but
        the naming is kept for backward compatibility.
        See _create_administrator() for creating
        a staff user with administrator group.
        """
        opts = dict(
            username="admin", email="admin@admin.com", is_superuser=True, is_staff=True
        )
        opts.update(kwargs)
        return self._create_user(**opts)

    def _create_org(self, **kwargs):
        options = {"name": "test org", "is_active": True, "slug": "test-org"}
        options.update(kwargs)
        org = Organization.objects.create(**options)
        return org

    def _create_operator_with_user_permissions(self, organizations=[], **kwargs):
        """
        Creates a staff user with the operator group and
        additional privileges to manage users
        """
        operator = self._create_operator(organizations, **kwargs)
        user_permissions = Permission.objects.filter(codename__endswith="user")
        operator.user_permissions.add(*user_permissions)
        operator.organizations_dict  # force caching
        return operator

    def _create_operator(self, organizations=[], **kwargs):
        """
        Creates a staff user with the operator group
        """
        opts = dict(
            username="operator",
            password="tester",
            email="operator@test.com",
            is_staff=True,
            birth_date=date(1987, 3, 23),
        )
        opts.update(kwargs)
        operator = User.objects.create_user(**opts)
        groups = Group.objects.filter(name="Operator")
        operator.groups.set(groups)
        for organization in organizations:
            OrganizationUser.objects.create(
                user=operator, organization=organization, is_admin=True
            )
        operator.organizations_dict  # force caching
        return operator

    def _create_administrator(self, organizations=[], **kwargs):
        """
        Creates a staff user with the administrator group
        """
        opts = dict(
            username="administrator",
            password="tester",
            email="administrator@test.com",
            is_staff=True,
        )
        opts.update(kwargs)
        administrator = User.objects.create_user(**opts)
        groups = Group.objects.filter(name="Administrator")
        administrator.groups.set(groups)
        for organization in organizations:
            OrganizationUser.objects.create(
                user=administrator, organization=organization, is_admin=True
            )
        administrator.organizations_dict  # force caching
        return administrator

    def _get_org(self, org_name="test org"):
        try:
            return Organization.objects.get(name=org_name)
        except Organization.DoesNotExist:
            return self._create_org(name=org_name)

    def _get_user(self, username="tester"):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self._create_user()

    def _get_admin(self, username="admin"):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self._create_admin()

    def _get_operator(self, username="operator"):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return self._create_operator()

    def _create_org_user(self, **kwargs):
        options = {
            "organization": self._get_org(),
            "is_admin": False,
            "user": self._get_user(),
        }
        options.update(kwargs)
        org = OrganizationUser.objects.create(**options)
        return org

    def _get_org_user(self):
        try:
            return OrganizationUser.objects.get(
                user=self._get_user(), organization=self._get_org()
            )
        except OrganizationUser.DoesNotExist:
            return self._create_org_user()

    def _create_org_owner(self, **kwargs):
        options = {
            "organization_user": self._get_org_user(),
            "organization": self._get_org(),
        }
        options.update(kwargs)
        org_owner = OrganizationOwner.objects.create(**options)
        return org_owner


class TestMultitenantAdminMixin(TestOrganizationMixin):
    def setUp(self):
        admin = self._create_admin(password="tester")
        admin.organizations_dict  # force caching

    def _login(self, username="admin", password="tester"):
        self.client.login(username=username, password=password)

    def _logout(self):
        self.client.logout()

    def _test_multitenant_admin(
        self, url, visible, hidden, select_widget=False, administrator=False
    ):
        """
        reusable test function that ensures different users
        can see the right objects.
        an operator with limited permissions will not be able
        to see the elements contained in ``hidden``, while
        a superuser can see everything.
        """
        if administrator:
            self._login(username="administrator", password="tester")
        else:
            self._login(username="operator", password="tester")
        response = self.client.get(url)

        # utility format function
        def _f(el, select_widget=False):
            if select_widget:
                return "{0}</option>".format(el)
            return el

        # ensure elements in visible list are visible to operator
        for el in visible:
            with self.subTest(el):
                self.assertContains(
                    response, _f(el, select_widget), msg_prefix="[operator contains]"
                )
        # ensure elements in hidden list are not visible to operator
        for el in hidden:
            with self.subTest(el):
                self.assertNotContains(
                    response,
                    _f(el, select_widget),
                    msg_prefix="[operator not-contains]",
                )

        # now become superuser
        self._logout()
        self._login(username="admin", password="tester")
        response = self.client.get(url)
        # ensure all elements are visible to superuser
        all_elements = visible + hidden
        for el in all_elements:
            self.assertContains(
                response, _f(el, select_widget), msg_prefix="[superuser contains]"
            )

    def _test_recoverlist_operator_403(self, app_label, model_label):
        self._login(username="operator", password="tester")
        response = self.client.get(
            reverse("admin:{0}_{1}_recoverlist".format(app_label, model_label))
        )
        self.assertEqual(response.status_code, 403)

    def _test_org_admin_create_shareable_object(
        self,
        path,
        payload,
        model,
        expected_count=0,
        user=None,
        error_message=None,
        raises_error=True,
    ):
        """
        Verifies a non-superuser cannot create a shareable object
        """
        if not user:
            user = self._create_administrator(organizations=[self._get_org()])
        self.client.force_login(user)
        response = self.client.post(
            path,
            data=payload,
            follow=True,
        )
        if raises_error:
            error_message = error_message or (
                '<div class="form-row errors field-organization">\n'
                '            <ul class="errorlist"{}>'
                "<li>This field is required.</li></ul>"
            ).format(' id="id_organization_error"' if django.VERSION >= (5, 2) else "")
            self.assertContains(response, error_message)
        self.assertEqual(model.objects.count(), expected_count)

    def _test_org_admin_view_shareable_object(
        self, path, user=None, expected_element=None
    ):
        """
        Verifies a non-superuser can view a shareable object
        """
        if not user:
            user = self._create_administrator(organizations=[self._get_org()])
        self.client.force_login(user)
        response = self.client.get(path, follow=True)
        self.assertEqual(response.status_code, 200)
        if not expected_element:
            expected_element = (
                '<div class="form-row field-organization">\n\n\n<div>\n\n'
                '<div class="flex-container">\n\n'
                "<label>Organization:</label>\n\n"
                '<div class="readonly">-</div>\n\n\n'
                "</div>\n\n</div>\n\n\n</div>"
            )
        self.assertContains(response, expected_element, html=True)

    def _test_object_organization_fk_autocomplete_view(
        self,
        model,
    ):
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        path = self._get_autocomplete_view_path(app_label, model_name, "organization")
        org = self._get_org()
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = self._create_admin()
        org_admin = self._create_administrator(organizations=[org])

        with self.subTest("Org admin should only see their own org"):
            self.client.force_login(org_admin)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, org.name)
            self.assertNotContains(response, SHARED_SYSTEMWIDE_LABEL)

        with self.subTest("Superuser should see all orgs and shared label"):
            self.client.force_login(admin)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, org.name)
            self.assertContains(response, SHARED_SYSTEMWIDE_LABEL)

    def _get_autocomplete_view_path(
        self, app_label, model_name, field_name, is_filter=False
    ):
        path = reverse("admin:ow-auto-filter")
        return (
            f"{path}?app_label={app_label}"
            f"&model_name={model_name}&field_name={field_name}"
            "{}".format("&is_filter=true" if is_filter else "")
        )
