import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from swapper import load_model

from openwisp_users.api.permissions import DisabledOrgReadOnly
from openwisp_users.api.throttling import AuthRateThrottle

from ..models import Shelf, Template
from ..serializers import BookManagerSerializer
from ..views import TemplateDetailView
from .mixins import TestMultitenancyMixin

User = get_user_model()
Group = load_model("openwisp_users", "Group")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")


class TestPermissionClasses(TestMultitenancyMixin, TestCase):
    def setUp(self):
        self._original_rate = AuthRateThrottle.rate
        self.addCleanup(setattr, AuthRateThrottle, "rate", self._original_rate)
        AuthRateThrottle.rate = None
        self.template_model = Template
        self.member_url = reverse("test_api_member_view")
        self.manager_url = reverse("test_api_manager_view")
        self.owner_url = reverse("test_api_owner_view")

    def test_operator_none(self):
        self._get_operator()
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("Organization Member"):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest("Organization Manager"):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest("Organization Owner"):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_member(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("Organization Member"):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Manager"):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest("Organization Owner"):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_manager(self):
        operator = self._get_operator()
        # First user is automatically owner, so created dummy
        # user to keep operator as manager only.
        self._create_org_user(user=self._get_user(), is_admin=True)
        self._create_org_user(user=operator, is_admin=True)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("Organization Member"):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Manager"):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Owner"):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 403)

    def test_operator_owner(self):
        operator = self._get_operator()
        # First user is automatically owner
        self._create_org_user(user=operator, is_admin=True)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("Organization Member"):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Manager"):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Owner"):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 200)

    def test_superuser(self):
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("Organization Member"):
            response = self.client.get(self.member_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Manager"):
            response = self.client.get(self.manager_url, **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Organization Owner"):
            response = self.client.get(self.owner_url, **auth)
            self.assertEqual(response.status_code, 200)

    def test_base_org_perm_fails(self):
        admin = self._get_operator()
        token = self._obtain_auth_token(username=admin)
        self.client.force_login(admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        base_org_permissions_url = reverse("test_base_org_permission_view")
        with self.assertRaises(NotImplementedError) as error:
            self.client.get(base_org_permissions_url, **auth)
        self.assertIn("Please use one of the child classes", str(error.exception))

    def test_organization_field_with_parent(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("test_organization_field_view"), **auth)
        self.assertEqual(response.status_code, 200)

    def test_organization_field_with_errored_parent(self):
        operator = self._get_operator()
        self._create_org_user(user=operator)
        token = self._obtain_auth_token()
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.assertRaises(AttributeError) as error:
            self.client.get(reverse("test_error_field_view"), **auth)
        self.assertIn("Organization not found", str(error.exception))

    def _get_auth_template(self, user, org1):
        OrganizationUser.objects.create(user=user, organization=org1, is_admin=True)
        self.client.force_login(user)
        token = self._obtain_auth_token(user)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        t1 = self._create_template(organization=org1)
        return (auth, t1)

    def test_view_permission_with_operator(self):
        user = self._get_user()
        operator_group = Group.objects.filter(name="Operator")
        user.groups.set(operator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest("Get Template List"):
            response = self.client.get(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, 403)
        with self.subTest("Get Template Detail"):
            response = self.client.get(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 403)

    def test_view_permission_with_administrator(self):
        user = self._get_user()
        administrator_group = Group.objects.get(name="Administrator")
        change_perm = Permission.objects.get(codename="change_template")
        administrator_group.permissions.set([])
        administrator_group.permissions.add(change_perm)
        user.groups.add(administrator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest("Get Template List"):
            response = self.client.get(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Get Template Detail"):
            response = self.client.get(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)
        permissions = administrator_group.permissions.values_list("codename", flat=True)
        self.assertFalse("view_template" in permissions)
        self.assertTrue("change_template" in permissions)

    def test_view_permission_with_operator_having_view_perm(self):
        user = self._get_user()
        operator_group = Group.objects.get(name="Operator")
        view_perm = Permission.objects.filter(codename="view_template")
        operator_group.permissions.set(view_perm)
        user.groups.add(operator_group)
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest("Get Template List"):
            response = self.client.get(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Get Template Detail"):
            response = self.client.get(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)
        with self.subTest("Change Template Detail"):
            data = {"name": "change-template"}
            response = self.client.patch(
                reverse("test_template_detail", args=[t1.pk]), data, **auth
            )
            self.assertEqual(response.status_code, 403)
        with self.subTest("Delete Template"):
            response = self.client.delete(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 403)

    def test_view_django_model_permission_with_view_perm(self):
        user = self._get_user()
        user_permissions = Permission.objects.filter(codename="view_template")
        user.user_permissions.add(*user_permissions)
        user.organizations_dict  # force caching
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest("Get Template List"):
            response = self.client.get(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Get Template Detail"):
            response = self.client.get(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)

    def test_view_django_model_permission_with_change_perm(self):
        user = self._get_user()
        user_permissions = Permission.objects.filter(codename="change_template")
        user.user_permissions.add(*user_permissions)
        user.organizations_dict  # force caching
        org1 = self._get_org()
        auth, t1 = self._get_auth_template(user, org1)
        with self.subTest("Get Template List"):
            response = self.client.get(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, 200)
        with self.subTest("Get Template Detail"):
            response = self.client.get(
                reverse("test_template_detail", args=[t1.pk]), **auth
            )
            self.assertEqual(response.status_code, 200)

    def _test_access_shared_object(
        self, token, expected_templates_count=1, expected_status_codes={}
    ):
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        template = self._create_template(organization=None)

        with self.subTest("Test listing templates"):
            response = self.client.get(reverse("test_template_list"), **auth)
            data = response.data.copy()
            # Only check "templates" in response.
            if isinstance(data, dict):
                data.pop("detail", None)
            self.assertEqual(response.status_code, expected_status_codes["list"])
            self.assertEqual(len(data), expected_templates_count)

        with self.subTest("Test creating template"):
            response = self.client.post(
                reverse("test_template_list"),
                data={"name": "Test Template", "organization": None},
                content_type="application/json",
                **auth,
            )
            self.assertEqual(response.status_code, expected_status_codes["create"])
            if expected_status_codes["create"] == 400:
                self.assertEqual(
                    str(response.data["organization"][0]), "This field may not be null."
                )

        with self.subTest("Test retreiving template"):
            response = self.client.get(
                reverse("test_template_detail", args=[template.id]), **auth
            )
            self.assertEqual(response.status_code, expected_status_codes["retrieve"])

        with self.subTest("Test updating template"):
            response = self.client.put(
                reverse("test_template_detail", args=[template.id]),
                data={"name": "Name changed"},
                content_type="application/json",
                **auth,
            )
            self.assertEqual(response.status_code, expected_status_codes["update"])

        with self.subTest("Test deleting template"):
            response = self.client.delete(
                reverse("test_template_detail", args=[template.id]), **auth
            )
            self.assertEqual(response.status_code, expected_status_codes["delete"])

        with self.subTest("Test HEAD and OPTION methods"):
            response = self.client.head(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, expected_status_codes["head"])

            response = self.client.options(reverse("test_template_list"), **auth)
            self.assertEqual(response.status_code, expected_status_codes["option"])

    def test_superuser_access_shared_object(self):
        superuser = self._get_admin()
        token = self._obtain_auth_token(username=superuser)
        self._test_access_shared_object(
            token,
            expected_status_codes={
                "create": 201,
                "list": 200,
                "retrieve": 200,
                "update": 200,
                "delete": 204,
                "head": 200,
                "option": 200,
            },
        )

    def test_org_manager_access_shared_object(self):
        org_manager = self._create_administrator()
        token = self._obtain_auth_token(username=org_manager)
        # First user is automatically owner, so created dummy
        # user to keep operator as manager only.
        self._create_org_user(user=self._get_user(), is_admin=True)
        self._create_org_user(user=org_manager, is_admin=True)
        self._test_access_shared_object(
            token,
            expected_status_codes={
                "create": 400,
                "list": 200,
                "retrieve": 200,
                "update": 403,
                "delete": 403,
                "head": 200,
                "option": 200,
            },
        )

    def test_org_owner_access_shared_object(self):
        # The first admin of an organization automatically
        # becomes organization owner.
        org_owner = self._create_administrator(organizations=[self._get_org()])
        token = self._obtain_auth_token(username=org_owner)
        self._test_access_shared_object(
            token,
            expected_status_codes={
                "create": 400,
                "list": 200,
                "retrieve": 200,
                "update": 403,
                "delete": 403,
                "head": 200,
                "option": 200,
            },
        )

    def test_org_user_access_shared_object(self):
        # The test uses a user with operator permissions,
        # because Django's model permission will deny permissions
        # to the view and this test won't test "shared object" permissions.
        user = self._create_administrator()
        token = self._obtain_auth_token(username=user)
        self._create_org_user(user=user, is_admin=False)
        self._test_access_shared_object(
            token,
            expected_templates_count=0,
            expected_status_codes={
                "create": 400,
                "list": 200,
                "retrieve": 404,
                "update": 404,
                "delete": 404,
                "head": 200,
                "option": 200,
            },
        )

    def test_bare_protected_api_mixin_view_blocks_disabled_org_write(self):
        org = self._get_org()
        template = self._create_template(organization=org)
        org.is_active = False
        org.save()
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        detail_url = reverse("test_protected_template_detail", args=[template.pk])
        self._test_disabled_org_api_update(
            detail_url,
            auth,
            {"name": "renamed"},
            template,
            error_contains=str(DisabledOrgReadOnly.message),
        )
        self._test_disabled_org_api_retrieve(detail_url, auth)

    def test_disabled_org_read_only_permission(self):
        org = self._get_org()
        template = self._create_template(organization=org)
        org.is_active = False
        org.save()
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        detail_url = reverse("test_template_detail", args=[template.pk])
        allowed_url = reverse(
            "test_template_disabled_org_write_allowed_detail", args=[template.pk]
        )
        self._test_disabled_org_api_update(
            detail_url,
            auth,
            {"name": "renamed"},
            template,
            error_contains=str(DisabledOrgReadOnly.message),
        )
        self._test_disabled_org_api_retrieve(detail_url, auth)

        with self.subTest("opt-out view allows write"):
            response = self.client.put(
                allowed_url,
                data={"name": "renamed"},
                content_type="application/json",
                **auth,
            )
            self.assertEqual(response.status_code, 200)

        with self.subTest("shared object unaffected"):
            shared_template = self._create_template(
                name="shared-template", organization=None
            )
            shared_url = reverse("test_template_detail", args=[shared_template.pk])
            response = self.client.put(
                shared_url,
                data={"name": "shared-renamed"},
                content_type="application/json",
                **auth,
            )
            self.assertEqual(response.status_code, 200)

        with self.subTest("DELETE allowed"):
            response = self.client.delete(detail_url, **auth)
            self.assertEqual(response.status_code, 204)

    def test_disabled_org_api_crud_superuser_only(self):
        org = self._create_org(name="api-mixin-org")
        template = self._create_template(name="t-super", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_template_detail", args=[template.pk]),
            list_url=reverse("test_template_list"),
            create_payload={"name": "t-super-new", "organization": str(org.pk)},
            update_payload={"name": "t-super-upd"},
            roles=("superuser",),
        )

    def test_disabled_org_api_crud_org_admin_loses_access(self):
        org = self._create_org(name="api-mixin-org-oa")
        template = self._create_template(name="t-oa", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_template_detail", args=[template.pk]),
            list_url=reverse("test_template_list"),
            create_payload={"name": "t-oa-new", "organization": str(org.pk)},
            update_payload={"name": "t-oa-upd"},
            roles=("org_admin",),
            org_admin_expected={
                "list": {"status": 200, "object_present": False},
                "retrieve": {"status": 404},
                "create": {
                    "status": 400,
                    "error_field": "organization",
                    "error_contains": "does not exist or is disabled",
                },
                "update": {"status": 404, "unchanged": True},
                "delete": {"status": 404, "exists_after": True},
            },
        )

    def test_disabled_org_api_crud_both_roles(self):
        org = self._create_org(name="api-mixin-org-both")
        template = self._create_template(name="t-both", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_template_detail", args=[template.pk]),
            list_url=reverse("test_template_list"),
            create_payload={"name": "t-both-new", "organization": str(org.pk)},
            update_payload={"name": "t-both-upd"},
            org_admin_expected={
                "list": {"status": 200, "object_present": False},
                "retrieve": {"status": 404},
                "create": {
                    "status": 400,
                    "error_field": "organization",
                    "error_contains": "does not exist or is disabled",
                },
                "update": {"status": 404, "unchanged": True},
                "delete": {"status": 404, "exists_after": True},
            },
        )

    def test_disabled_org_api_crud_session_auth(self):
        org = self._create_org(name="api-mixin-org-session")
        template = self._create_template(name="t-sess", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_protected_template_detail", args=[template.pk]),
            roles=("superuser",),
            operations=("retrieve", "update"),
            update_payload={"name": "t-sess-upd"},
            auth_mechanism="session",
        )

    def test_disabled_org_api_crud_bare_protected_mixin(self):
        org = self._create_org(name="api-mixin-org-bare")
        template = self._create_template(name="t-bare", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_protected_template_detail", args=[template.pk]),
            roles=("superuser",),
            operations=("retrieve", "update"),
            update_payload={"name": "t-bare-upd"},
        )

    def test_disabled_org_api_crud_operations_subset(self):
        org = self._create_org(name="api-mixin-org-subset")
        template = self._create_template(name="t-subset", organization=org)
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=reverse("test_template_detail", args=[template.pk]),
            roles=("superuser",),
            operations=("retrieve",),
        )
        self.assertEqual(
            self.template_model.objects.filter(pk=template.pk).exists(), True
        )

    def test_disabled_org_api_crud_opt_out_override(self):
        org = self._create_org(name="api-mixin-org-optout")
        template = self._create_template(name="t-optout", organization=org)
        detail_url = reverse("test_template_detail", args=[template.pk])
        allowed_url = reverse(
            "test_template_disabled_org_write_allowed_detail", args=[template.pk]
        )
        org.is_active = False
        org.save()
        self._test_disabled_org_api_crud(
            template,
            detail_url=detail_url,
            roles=("superuser",),
            operations=("retrieve", "update"),
            update_payload={"name": "renamed"},
        )
        self._test_disabled_org_api_crud(
            template,
            detail_url=allowed_url,
            roles=("superuser",),
            operations=("update",),
            update_payload={"name": "t-optout-up"},
            superuser_expected={"update": {"status": 200, "unchanged": False}},
        )
        template.refresh_from_db()
        self.assertEqual(template.name, "t-optout-up")

        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        with self.subTest("shared object unaffected"):
            shared_template = self._create_template(
                name="shared-template", organization=None
            )
            shared_url = reverse("test_template_detail", args=[shared_template.pk])
            response = self.client.put(
                shared_url,
                data={"name": "shared-renamed"},
                content_type="application/json",
                **auth,
            )
            self.assertEqual(response.status_code, 200)

        with self.subTest("DELETE allowed"):
            response = self.client.delete(detail_url, **auth)
            self.assertEqual(response.status_code, 204)

    def test_organization_field_excludes_disabled_org(self):
        disabled_org = self._create_org(name="disabled-org", is_active=False)
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        auth = dict(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.post(
            reverse("test_template_list"),
            data={"name": "t1", "organization": str(disabled_org.pk)},
            content_type="application/json",
            **auth,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "does not exist or is disabled", str(response.data["organization"][0])
        )
        self.assertEqual(self.template_model.objects.filter(name="t1").count(), 0)

    def test_fk_field_excludes_disabled_org_for_superuser(self):
        active_org = self._create_org(name="active-fk-org")
        disabled_org = self._create_org(name="disabled-fk-org", is_active=False)
        admin = self._get_admin()
        shelf_active = Shelf(name="shelf-active", organization=active_org)
        shelf_active.full_clean()
        shelf_active.save()
        shelf_disabled = Shelf(name="shelf-disabled", organization=disabled_org)
        shelf_disabled.full_clean()
        shelf_disabled.save()
        request = APIRequestFactory().get("/")
        request.user = admin
        serializer = BookManagerSerializer(context={"request": request})
        shelf_pks = set(
            serializer.fields["shelf"].queryset.values_list("pk", flat=True)
        )
        self.assertIn(shelf_active.pk, shelf_pks)
        self.assertNotIn(shelf_disabled.pk, shelf_pks)

    def test_disabled_org_read_only_denies_on_misconfigured_field(self):
        class BrokenOrgFieldTemplateDetailView(TemplateDetailView):
            # A bad relation path must fail closed to avoid granting write access.
            organization_field = "nonexistent_field"

        org = self._get_org()
        template = self._create_template(organization=org, name="original-name")
        admin = self._get_admin()
        token = self._obtain_auth_token(username=admin)
        request = RequestFactory().put(
            "/",
            data=json.dumps({"name": "renamed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        response = BrokenOrgFieldTemplateDetailView.as_view()(request, pk=template.pk)
        response.render()
        self.assertEqual(response.status_code, 403)
        template.refresh_from_db()
        self.assertEqual(template.name, "original-name")

    def test_disabled_org_read_only_select_related_valid_field(self):
        org = self._get_org()
        self._create_template(organization=org)
        admin = self._get_admin()
        request = APIRequestFactory().get("/")
        request.user = admin
        view = TemplateDetailView()
        view.request = request
        queryset = view.get_queryset()
        self.assertIn("organization", queryset.query.select_related)
