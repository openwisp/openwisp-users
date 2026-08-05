from django.test import TestCase
from django.urls import reverse

from openwisp_users.api.permissions import DisabledOrgReadOnly
from openwisp_users.tests.utils import TestDisabledOrgMixin, TestMultitenantAdminMixin


class AuthenticationMixin:
    def _obtain_auth_token(self, username="operator", password="tester"):
        params = {"username": username, "password": password}
        url = reverse("users:user_auth_token")
        response = self.client.post(url, params)
        return response.data["token"]


class TestDisabledOrgApiMixin(TestDisabledOrgMixin):
    """
    Reusable assertions for the REST API's disabled-organization guard
    (``DisabledOrgReadOnly`` plus the ``organization`` field filtering
    performed by the ``FilterSerializerByOrganization`` subclasses), for
    downstream OpenWISP modules to exercise against their own
    org-scoped API views without re-implementing the request plumbing.

    Must be composed alongside ``AuthenticationMixin`` (for
    ``_obtain_auth_token``), which every existing composite in this
    codebase using this mixin already includes.

    Prerequisite (not enforced by this mixin): the serializer behind the
    create payload must filter its ``organization`` field to active
    organizations for the "create" assertion below to hold - one of
    ``FilterSerializerByOrgManaged``/``Membership``/``Owned``, or an
    equivalent explicit queryset, see
    ``openwisp_users/api/mixins.py:FilterSerializerByOrganization``.

    Note: the default expectations assume the view uses
    ``IsOrganizationManager`` in its ``permission_classes``. Once an
    organization is disabled, it drops out of every user's
    ``organizations_managed`` (see ``organizations_dict``), so an
    "org_admin" who managed only that organization has an empty
    ``organizations_managed`` list. ``IsOrganizationManager.has_permission()``
    blocks every request with 403 because the user no longer manages any
    active organization. The superuser bypasses this check but is still
    blocked by ``DisabledOrgReadOnly`` on update. This is why the two
    roles have different default expectations below.
    """

    disabled_org_api_default_expectations = {
        "superuser": {
            "list": {"status": 200, "object_present": True},
            "retrieve": {"status": 200},
            "create": {
                "status": 400,
                "error_field": "organization",
                "error_contains": "does not exist or is disabled",
            },
            "update": {
                "status": 403,
                "unchanged": True,
                "error_contains": str(DisabledOrgReadOnly.message),
            },
            "delete": {"status": 204, "exists_after": False},
        },
        "org_admin": {
            "list": {"status": 403},
            "retrieve": {"status": 403},
            "create": {"status": 403},
            "update": {"status": 403, "unchanged": True},
            "delete": {"status": 403, "exists_after": True},
        },
    }

    def _disabled_org_api_auth(self, user, mechanism="bearer", password="tester"):
        if mechanism == "bearer":
            token = self._obtain_auth_token(username=user.username, password=password)
            return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        if mechanism == "session":
            self.client.force_login(user)
            return {}
        raise ValueError(f"Unknown auth mechanism: {mechanism!r}")

    def _test_disabled_org_api_list(
        self, url, auth, obj, status=200, object_present=True, id_field="id"
    ):
        response = self.client.get(url, **auth)
        self.assertEqual(response.status_code, status)
        if status != 200:
            return
        data = response.data
        results = data["results"] if isinstance(data, dict) else data
        obj_id = str(getattr(obj, id_field))
        present = any(str(item.get(id_field)) == obj_id for item in results)
        self.assertEqual(present, object_present)

    def _test_disabled_org_api_retrieve(self, url, auth, status=200):
        response = self.client.get(url, **auth)
        self.assertEqual(response.status_code, status)

    def _test_disabled_org_api_create(
        self,
        url,
        auth,
        payload,
        status=400,
        error_field="organization",
        error_contains=None,
    ):
        response = self.client.post(
            url, data=payload, content_type="application/json", **auth
        )
        self.assertEqual(response.status_code, status)
        if error_contains:
            self.assertIn(error_contains, str(response.data[error_field][0]))

    def _test_disabled_org_api_update(
        self,
        url,
        auth,
        payload,
        obj,
        status=403,
        unchanged=True,
        unchanged_field="name",
        error_contains=None,
        methods=("put", "patch"),
    ):
        for method in methods:
            with self.subTest(method=method):
                if unchanged:
                    before = getattr(obj, unchanged_field)
                response = getattr(self.client, method)(
                    url, data=payload, content_type="application/json", **auth
                )
                self.assertEqual(response.status_code, status)
                if error_contains:
                    self.assertEqual(str(response.data["detail"]), error_contains)
                if unchanged:
                    obj.refresh_from_db()
                    self.assertEqual(getattr(obj, unchanged_field), before)

    def _test_disabled_org_api_delete(
        self, url, auth, model, pk, status=204, exists_after=False
    ):
        response = self.client.delete(url, **auth)
        self.assertEqual(response.status_code, status)
        self.assertEqual(model.objects.filter(pk=pk).exists(), exists_after)

    def _test_disabled_org_api_crud(
        self,
        obj,
        detail_url,
        list_url=None,
        create_payload=None,
        update_payload=None,
        roles=("org_admin", "superuser"),
        operations=("list", "retrieve", "create", "update", "delete"),
        org_admin_expected=None,
        superuser_expected=None,
        auth_mechanism="bearer",
        unchanged_field="name",
        organization=None,
    ):
        organization = organization or getattr(obj, "organization", None)
        specs = {
            "org_admin": {
                **self.disabled_org_api_default_expectations["org_admin"],
                **(org_admin_expected or {}),
            },
            "superuser": {
                **self.disabled_org_api_default_expectations["superuser"],
                **(superuser_expected or {}),
            },
        }
        model = type(obj)
        pk = obj.pk
        for role in roles:
            user = self._disabled_org_role_user(role, organization=organization)
            auth = self._disabled_org_api_auth(user, mechanism=auth_mechanism)
            for operation in operations:
                with self.subTest(role=role, operation=operation):
                    spec = specs[role][operation]
                    if operation == "list":
                        self._test_disabled_org_api_list(list_url, auth, obj, **spec)
                    elif operation == "retrieve":
                        self._test_disabled_org_api_retrieve(detail_url, auth, **spec)
                    elif operation == "create":
                        self._test_disabled_org_api_create(
                            list_url, auth, create_payload, **spec
                        )
                    elif operation == "update":
                        self._test_disabled_org_api_update(
                            detail_url,
                            auth,
                            update_payload,
                            obj,
                            unchanged_field=unchanged_field,
                            **spec,
                        )
                    elif operation == "delete":
                        self._test_disabled_org_api_delete(
                            detail_url, auth, model, pk, **spec
                        )
                    else:
                        raise ValueError(f"Unknown operation: {operation!r}")


class APITestCase(
    TestMultitenantAdminMixin, TestDisabledOrgApiMixin, AuthenticationMixin, TestCase
):
    pass
