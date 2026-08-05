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
    """
    Shared helper for the disabled-organization admin and API test
    mixins: creating the "superuser" / "org_admin" role users.
    """

    def _disabled_org_role_user(self, role, organization=None, **kwargs):
        """
        Returns the user impersonating ``role``:
        "superuser" is a superuser (``_get_admin()``/``_create_admin()``
        when ``kwargs`` is given, to avoid username collisions across
        multiple calls in the same test); "org_admin" is a staff user in
        the "Administrator" group who is (or, since ``organization`` is
        disabled, *was*) its manager (``_create_administrator``, i.e. an
        ``OrganizationUser`` with ``is_admin=True`` - this codebase's
        existing meaning of "organization admin", not ``is_staff``).
        """
        if role == "superuser":
            return self._create_admin(**kwargs) if kwargs else self._get_admin()
        if role == "org_admin":
            if organization is None:
                raise ValueError('role "org_admin" requires organization=')
            return self._create_administrator(organizations=[organization], **kwargs)
        raise ValueError(f"Unknown role: {role!r}")


class TestDisabledOrgAdminMixin(TestDisabledOrgMixin):
    """
    Reusable assertions for ``MultitenantAdminMixin``'s
    disabled-organization write protection (``has_change_permission`` /
    ``_edit_form``), for downstream OpenWISP modules to exercise against
    their own org-scoped ``ModelAdmin`` classes without re-implementing
    the request plumbing. ``obj`` must already belong to a disabled
    organization (or be reachable through ``multitenant_parent`` from
    one) before any of these are called; creating/disabling the
    organization is left to the caller.

    Note: once an organization is disabled, it drops out of every
    user's ``organizations_managed`` (see ``organizations_dict``), so an
    "org_admin" who managed it loses queryset visibility of its objects
    entirely: admin views 404 rather than 403. This is why the two
    roles have different default expectations below.
    """

    disabled_org_admin_default_expectations = {
        "superuser": {
            "view": {"status": 200},
            "change": {"status": 403, "unchanged": True},
            "delete": {"status": 200, "exists_after": False},
        },
        "org_admin": {
            # the object is filtered out of get_queryset() before any
            # permission check runs, so Django admin's own "doesn't
            # exist" handling kicks in instead of DisabledOrgReadOnly's
            # 403: a raw (unfollowed) GET redirects (302) to the admin
            # index; a POST change/delete redirects the same way, which
            # this mixin follows (matching how a successful change/
            # delete is asserted for superuser), landing on a 200 admin
            # index page in both cases - "unchanged"/"exists_after" is
            # what actually proves nothing happened, not the status code
            "view": {"status": 302},
            "change": {"status": 200, "unchanged": True},
            "delete": {"status": 200, "exists_after": True},
        },
    }

    def _get_disabled_org_admin_urls(self, obj, admin_site="admin"):
        """
        Derives the "view"/"change"/"delete" admin URLs for ``obj`` from
        ``obj._meta.app_label``/``model_name``, following Django's
        standard ``{admin_site}:{app_label}_{model_name}_{change,delete}``
        naming ("view" and "change" are the same URL, GET vs POST).
        """
        meta = obj._meta
        change_url = reverse(
            f"{admin_site}:{meta.app_label}_{meta.model_name}_change", args=[obj.pk]
        )
        delete_url = reverse(
            f"{admin_site}:{meta.app_label}_{meta.model_name}_delete", args=[obj.pk]
        )
        return {"view": change_url, "change": change_url, "delete": delete_url}

    def _test_disabled_org_admin_view(self, url, status=200):
        """GETs ``url`` (the change view) and asserts the status code."""
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
        """
        POSTs ``change_data`` to ``url`` (``follow=True``) and asserts
        ``status``. When ``unchanged`` is True, also asserts ``obj``'s
        ``unchanged_field`` still equals its pre-POST value after
        ``obj.refresh_from_db()`` - i.e. the blocked write did not
        silently apply.
        """
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
        """
        POSTs the delete confirmation and asserts ``status`` and whether
        ``model.objects.filter(pk=pk).exists()`` equals ``exists_after``.
        """
        response = self.client.post(url, {"post": "yes"}, follow=True)
        self.assertEqual(response.status_code, status)
        self.assertEqual(model.objects.filter(pk=pk).exists(), exists_after)

    def _test_disabled_org_admin_org_field_excludes_disabled(
        self,
        url,
        disabled_org,
        roles=("superuser",),
        organization=None,
        role_kwargs=None,
    ):
        """
        For each role, GETs ``url`` (an add or change view) and asserts
        ``disabled_org`` is never offered as an ``organization`` choice.
        Testing the "org_admin" role requires ``organization=`` to be a
        *different*, still-active organization the role manages (an
        org_admin whose only organization is the disabled one loses
        ``has_add_permission`` entirely, so there would be no form to
        inspect).
        """
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
        operations=("view", "change", "delete"),
        organization=None,
        org_admin_expected=None,
        superuser_expected=None,
        unchanged_field="name",
    ):
        """
        Umbrella test: for each role in ``roles``, logs the role's user
        in and runs each operation in ``operations`` against ``obj``,
        asserting the outcome from ``disabled_org_admin_default_expectations``
        (per-role, shallow-overridden by ``org_admin_expected``/
        ``superuser_expected``). For anything this can't express (a
        non-standard admin site/URL, extra ``_disabled_org_role_user``
        kwargs, skipping a role/operation entirely), call
        ``_test_disabled_org_admin_view``/``_change``/``_delete``
        directly instead.

        The default role order is "org_admin" before "superuser" because
        with the default expectations only the superuser's "delete"
        actually removes ``obj`` (the org_admin's is a no-op, the object
        never being in their queryset); a custom ``roles=`` combination
        where a different role's action genuinely mutates or removes
        ``obj`` should put that role last for the same reason.

        ``organization`` defaults to ``getattr(obj, "organization", None)``;
        pass it explicitly for models reached through
        ``multitenant_parent`` (it has no direct ``organization``
        attribute).
        """
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
        """
        Generic proof that ``model_admin.get_inline_instances`` write-
        protects every inline attached to ``disabled_obj`` (an instance
        whose disabled organization is what triggers the guard - for
        ``OrganizationAdmin`` that is the ``Organization`` itself; for a
        downstream org-scoped ``ModelAdmin`` it is the parent object
        belonging to the disabled org): add/change permission denied,
        delete permission preserved. ``inline_models`` optionally
        narrows the assertion to a subset of inline classes (matched via
        ``isinstance``) when only some of a ``ModelAdmin``'s inlines are
        expected to be write-protected. When ``active_obj`` is given,
        also asserts its inlines stay fully writable, proving the guard
        is specific to the disabled organization rather than blanket.
        """
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

    def _get_autocomplete_view_path(self, app_label, model_name, field_name):
        path = reverse("admin:ow-auto-filter")
        return (
            f"{path}?app_label={app_label}"
            f"&model_name={model_name}&field_name={field_name}"
        )
