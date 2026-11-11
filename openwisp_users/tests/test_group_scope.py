import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from swapper import load_model

from ..admin import UserAdmin
from ..multitenancy import get_assignable_groups
from .utils import TestOrganizationMixin

Group = load_model("openwisp_users", "Group")
GroupScope = load_model("openwisp_users", "GroupScope")
Organization = load_model("openwisp_users", "Organization")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
User = get_user_model()


class TestGroupScope(TestOrganizationMixin, TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", password="password", email="admin@test.org"
        )
        self.org_x = self._create_org(name="Org X")
        self.org_y = self._create_org(name="Org Y")

        # Create groups with different scopes
        self.group_global = Group.objects.create(name="Global Group")
        scope_global, _ = GroupScope.objects.get_or_create(group=self.group_global)
        scope_global.assignable_to = "everyone"
        scope_global.save()

        self.group_superuser = Group.objects.create(name="Superuser Group")
        scope_su, _ = GroupScope.objects.get_or_create(group=self.group_superuser)
        scope_su.assignable_to = "superusers"
        scope_su.save()

        self.group_org_x = Group.objects.create(name="Org X Group")
        scope_x, _ = GroupScope.objects.get_or_create(group=self.group_org_x)
        scope_x.assignable_to = "organizations"
        scope_x.save()
        scope_x.organizations.add(self.org_x)

        self.group_org_y = Group.objects.create(name="Org Y Group")
        scope_y, _ = GroupScope.objects.get_or_create(group=self.group_org_y)
        scope_y.assignable_to = "organizations"
        scope_y.save()
        scope_y.organizations.add(self.org_y)

        # Create manager for Org X
        self.manager_x = self._create_user(
            username="manager_x", email="manager_x@test.org", is_staff=True
        )
        self._create_org_user(
            user=self.manager_x, organization=self.org_x, is_admin=True
        )
        # Give permissions to manage users
        for codename in ["add_user", "change_user", "view_user"]:
            perm = Permission.objects.filter(codename=codename).first()
            if perm:
                self.manager_x.user_permissions.add(perm)

    def test_get_assignable_groups_superuser(self):
        assignable = get_assignable_groups(self.superuser)
        self.assertIn(self.group_global, assignable)
        self.assertIn(self.group_superuser, assignable)
        self.assertIn(self.group_org_x, assignable)
        self.assertIn(self.group_org_y, assignable)

    def test_get_assignable_groups_org_manager(self):
        assignable = get_assignable_groups(self.manager_x)
        self.assertIn(self.group_global, assignable)
        self.assertIn(self.group_org_x, assignable)
        self.assertNotIn(self.group_superuser, assignable)
        self.assertNotIn(self.group_org_y, assignable)

    def test_admin_formfield_for_manytomany(self):
        from django.contrib.admin.sites import AdminSite

        site = AdminSite()
        user_admin = UserAdmin(User, site)
        factory = RequestFactory()

        # For superuser:
        request_su = factory.get("/")
        request_su.user = self.superuser
        groups_field = User._meta.get_field("groups")
        formfield_su = user_admin.formfield_for_manytomany(groups_field, request_su)
        self.assertIn(self.group_superuser, formfield_su.queryset)
        self.assertIn(self.group_org_y, formfield_su.queryset)

        # For manager of Org X:
        request_mgr = factory.get("/")
        request_mgr.user = self.manager_x
        formfield_mgr = user_admin.formfield_for_manytomany(groups_field, request_mgr)
        self.assertIn(self.group_global, formfield_mgr.queryset)
        self.assertIn(self.group_org_x, formfield_mgr.queryset)
        self.assertNotIn(self.group_superuser, formfield_mgr.queryset)
        self.assertNotIn(self.group_org_y, formfield_mgr.queryset)

    def test_admin_user_form_validation(self):
        from django.contrib.admin.sites import AdminSite

        site = AdminSite()
        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.manager_x

        Form = user_admin.get_form(request)
        form = Form()

        # Manager assigning allowed group
        data_valid = {
            "is_staff": True,
            "groups": [self.group_org_x],
        }
        form.validate_user_groups(data_valid)

        # Manager assigning restricted group (superuser group)
        data_invalid = {
            "is_staff": True,
            "groups": [self.group_superuser],
        }
        with self.assertRaises(ValidationError) as ctx:
            form.validate_user_groups(data_invalid)
        self.assertIn("groups", ctx.exception.message_dict)

        # Manager assigning restricted group (Org Y group)
        data_invalid_y = {
            "is_staff": True,
            "groups": [self.group_org_y],
        }
        with self.assertRaises(ValidationError) as ctx:
            form.validate_user_groups(data_invalid_y)
        self.assertIn("groups", ctx.exception.message_dict)

    def test_api_user_creation_restriction(self):
        self.client.force_login(self.manager_x)
        url = reverse("users:user_list")

        # Try to assign restricted group (superuser only)
        payload_invalid = {
            "username": "new_user_fail",
            "email": "new_fail@test.org",
            "password": "ValidPassword123!",
            "is_staff": True,
            "groups": [self.group_superuser.pk],
            "organization_users": {
                "organization": str(self.org_x.pk),
                "is_admin": False,
            },
        }
        response = self.client.post(
            url, json.dumps(payload_invalid), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("groups", response.data)

        # Try to assign restricted group (different org)
        payload_invalid_y = {
            "username": "new_user_fail_y",
            "email": "new_fail_y@test.org",
            "password": "ValidPassword123!",
            "is_staff": True,
            "groups": [self.group_org_y.pk],
            "organization_users": {
                "organization": str(self.org_x.pk),
                "is_admin": False,
            },
        }
        response = self.client.post(
            url, json.dumps(payload_invalid_y), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("groups", response.data)

        # Assign allowed group (Org X)
        payload_valid = {
            "username": "new_user_ok",
            "email": "new_ok@test.org",
            "password": "ValidPassword123!",
            "is_staff": True,
            "groups": [self.group_org_x.pk],
            "organization_users": {
                "organization": str(self.org_x.pk),
                "is_admin": False,
            },
        }
        response = self.client.post(
            url, json.dumps(payload_valid), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_api_user_update_restriction(self):
        target_user = self._create_user(
            username="target_user", email="target@test.org", is_staff=True
        )
        self._create_org_user(user=target_user, organization=self.org_x, is_admin=False)

        self.client.force_login(self.manager_x)
        url = reverse("users:user_detail", args=[target_user.pk])

        # Try to update target user with restricted group
        response = self.client.patch(
            url,
            json.dumps({"groups": [self.group_superuser.pk]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("groups", response.data)

        # Update with allowed group
        response = self.client.patch(
            url,
            json.dumps({"groups": [self.group_org_x.pk]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.group_org_x, target_user.groups.all())
