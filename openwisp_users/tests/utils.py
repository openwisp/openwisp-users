from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse
from swapper import load_model

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


class TestDisabledOrgMixin(TestOrganizationMixin):
    """Shared setup for disabled-organization admin and API tests."""

    def _disabled_org_role_user(self, role, organization=None, **kwargs):
        """Use a former organization manager to exercise disabled-org access."""
        if role == "superuser":
            return self._create_admin(**kwargs) if kwargs else self._get_admin()
        if role == "org_admin":
            if organization is None:
                raise ValueError('role "org_admin" requires organization=')
            return self._create_administrator(organizations=[organization], **kwargs)
        raise ValueError(f"Unknown role: {role!r}")


class TestDisabledOrgAdminMixin(TestDisabledOrgMixin):
    """Reusable assertions for disabled-organization admin behavior.

    Callers must provide an object that already belongs to a disabled
    organization.
    """

    disabled_org_admin_default_expectations = {
        "superuser": {
            "view": {"status": 200},
            "change": {"status": 403, "unchanged": True},
            "delete": {"status": 200, "exists_after": False},
            # The organization field always excludes disabled organizations
            # on add, regardless of role or write-protection opt-out.
            "add": {"status": 200, "created": False},
        },
        "org_admin": {
            # The disabled object is outside the manager's queryset, so the
            # admin redirects instead of reaching the permission check.
            "view": {"status": 302},
            "change": {"status": 200, "unchanged": True},
            "delete": {"status": 200, "exists_after": True},
            # organizations_managed excludes disabled organizations, so an
            # org_admin whose only managed org is disabled has no add
            # permission at all.
            "add": {"status": 403, "created": False},
        },
    }

    def _get_disabled_org_admin_urls(self, obj, admin_site="admin"):
        meta = obj._meta
        change_url = reverse(
            f"{admin_site}:{meta.app_label}_{meta.model_name}_change", args=[obj.pk]
        )
        delete_url = reverse(
            f"{admin_site}:{meta.app_label}_{meta.model_name}_delete", args=[obj.pk]
        )
        add_url = reverse(f"{admin_site}:{meta.app_label}_{meta.model_name}_add")
        return {
            "view": change_url,
            "change": change_url,
            "delete": delete_url,
            "add": add_url,
        }

    def _test_disabled_org_admin_view(self, url, status=200):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status)

    def _test_disabled_org_admin_change(
        self,
        url,
        change_data,
        obj,
        status=403,
        unchanged=True,
        unchanged_field="name",
    ):
        if unchanged:
            before = getattr(obj, unchanged_field)
        response = self.client.post(url, change_data, follow=True)
        self.assertEqual(response.status_code, status)
        if unchanged:
            obj.refresh_from_db()
            self.assertEqual(getattr(obj, unchanged_field), before)

    def _test_disabled_org_admin_delete(
        self, url, model, pk, status=200, exists_after=False
    ):
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, status)
        self.assertEqual(model.objects.filter(pk=pk).exists(), exists_after)

    def _test_disabled_org_admin_add(
        self, url, create_data, model, status=200, created=False
    ):
        count_before = model.objects.count()
        response = self.client.post(url, create_data, follow=True)
        self.assertEqual(response.status_code, status)
        self.assertEqual(model.objects.count() > count_before, created)

    def _test_disabled_org_admin_org_field_excludes_disabled(
        self,
        url,
        disabled_org,
        roles=("superuser",),
        organization=None,
        role_kwargs=None,
    ):
        role_kwargs = role_kwargs or {}
        for role in roles:
            with self.subTest(role=role):
                user = self._disabled_org_role_user(
                    role, organization=organization, **role_kwargs.get(role, {})
                )
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertNotContains(response, f"{disabled_org.name}</option>")
                self.client.logout()

    def _test_disabled_org_admin_crud(
        self,
        obj,
        change_data,
        roles=("org_admin", "superuser"),
        operations=("view", "change", "delete", "add"),
        organization=None,
        org_admin_expected=None,
        superuser_expected=None,
        unchanged_field="name",
        create_data=None,
    ):
        """Run shared checks for direct or parent-linked organizations."""
        if create_data is None:
            operations = tuple(op for op in operations if op != "add")
        organization = organization or getattr(obj, "organization", None)
        urls = self._get_disabled_org_admin_urls(obj)
        specs = {
            "org_admin": {
                **self.disabled_org_admin_default_expectations["org_admin"],
                **(org_admin_expected or {}),
            },
            "superuser": {
                **self.disabled_org_admin_default_expectations["superuser"],
                **(superuser_expected or {}),
            },
        }
        for role in roles:
            user = self._disabled_org_role_user(role, organization=organization)
            self.client.force_login(user)
            for operation in operations:
                spec = specs[role][operation]
                with self.subTest(role=role, operation=operation):
                    if operation == "view":
                        self._test_disabled_org_admin_view(urls["view"], **spec)
                    elif operation == "change":
                        self._test_disabled_org_admin_change(
                            urls["change"],
                            change_data,
                            obj,
                            unchanged_field=unchanged_field,
                            **spec,
                        )
                    elif operation == "delete":
                        self._test_disabled_org_admin_delete(
                            urls["delete"], type(obj), obj.pk, **spec
                        )
                    elif operation == "add":
                        self._test_disabled_org_admin_add(
                            urls["add"], create_data, type(obj), **spec
                        )
                    else:
                        raise ValueError(f"Unknown operation: {operation!r}")
            self.client.logout()

    def _test_disabled_org_admin_inline_readonly(
        self,
        model_admin,
        disabled_obj,
        active_obj=None,
        inline_models=None,
        inline_admins=None,
        user=None,
    ):
        request = RequestFactory().get("/")
        request.user = user or self._get_admin()

        inlines = inline_admins or model_admin.get_inline_instances(
            request, disabled_obj
        )
        if inline_models is not None:
            inlines = [i for i in inlines if isinstance(i, inline_models)]
        self.assertNotEqual(inlines, [])
        for inline in inlines:
            self.assertEqual(inline.has_add_permission(request, disabled_obj), False)
            self.assertEqual(inline.has_change_permission(request, disabled_obj), False)
            self.assertEqual(inline.has_delete_permission(request, disabled_obj), True)

        if active_obj is not None:
            active_inlines = model_admin.get_inline_instances(request, active_obj)
            if inline_models is not None:
                active_inlines = [
                    i for i in active_inlines if isinstance(i, inline_models)
                ]
            for inline in active_inlines:
                self.assertEqual(
                    inline.has_change_permission(request, active_obj), True
                )


class TestMultitenantAdminMixin(TestDisabledOrgAdminMixin):
    def setUp(self):
        admin = self._create_admin(password="tester")
        admin.organizations_dict  # force caching
        super().setUp()

    def _login(self, username="admin", password="tester"):
        self.client.login(username=username, password=password)

    def _logout(self):
        self.client.logout()

    def _test_multitenant_admin(
        self,
        url,
        visible,
        hidden,
        select_widget=False,
        administrator=False,
        superuser_hidden=None,
    ):
        """
        reusable test function that ensures different users
        can see the right objects.
        an operator with limited permissions will not be able
        to see the elements contained in ``hidden``, while
        a superuser can see everything, except the elements in
        ``superuser_hidden`` (e.g. objects belonging to a disabled
        organization, which relation pickers exclude for everyone).
        """
        superuser_hidden = superuser_hidden or []
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
        # Relation pickers still hide disabled values from superusers.
        all_elements = [el for el in visible + hidden if el not in superuser_hidden]
        for el in all_elements:
            self.assertContains(
                response, _f(el, select_widget), msg_prefix="[superuser contains]"
            )
        for el in superuser_hidden:
            self.assertNotContains(
                response, _f(el, select_widget), msg_prefix="[superuser not-contains]"
            )

    def _test_recoverlist_operator_403(self, app_label, model_label):
        self._login(username="operator", password="tester")
        response = self.client.get(
            reverse("admin:{0}_{1}_recoverlist".format(app_label, model_label))
        )
        self.assertEqual(response.status_code, 403)

    def _get_autocomplete_view_path(self, app_label, model_name, field_name):
        path = reverse("admin:ow-auto-filter")
        return (
            f"{path}?app_label={app_label}"
            f"&model_name={model_name}&field_name={field_name}"
        )
