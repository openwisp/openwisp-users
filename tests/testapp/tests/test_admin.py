import os

import reversion
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from reversion.models import Version
from swapper import load_model

from openwisp_users.tests.utils import TestOrganizationMixin

from ..models import Template

Organization = load_model("openwisp_users", "Organization")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
OrganizationOwner = load_model("openwisp_users", "OrganizationOwner")
User = get_user_model()
Group = load_model("openwisp_users", "Group")


class TestUsersAdmin(TestOrganizationMixin, TestCase):
    app_label = (
        "openwisp_users" if not os.environ.get("SAMPLE_APP", False) else "sample_users"
    )

    def test_group_reversion(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        test_group = Group.objects.create()
        self.client.post(
            reverse(f"admin:{self.app_label}_group_change", args=(test_group.id,)),
            {"name": "test_group_v1"},
            follow=True,
        )
        r = self.client.get(
            reverse(f"admin:{self.app_label}_group_revision", args=(test_group.id, 1))
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<h1>Revert test_group_v1</h1>")

    def test_version_admin_revision_views_superuser_only(self):
        administrator = self._create_administrator([self._create_org()])
        administrator.user_permissions.add(
            *Permission.objects.filter(codename__endswith="_tag")
        )
        with reversion.create_revision():
            administrator.is_superuser = True
            administrator.save()
        User.objects.filter(pk=administrator.pk).update(is_superuser=False)
        version = Version.objects.get_for_object(administrator).first()
        self.client.force_login(administrator)
        for url in [
            reverse("admin:testapp_tag_revision", args=(version.object_id, version.pk)),
            reverse("admin:testapp_tag_recover", args=(version.pk,)),
            reverse("admin:testapp_tag_recoverlist"),
        ]:
            for method in ("get", "post"):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 403, f"{method} {url}")
        administrator.refresh_from_db()
        self.assertFalse(administrator.is_superuser)

    def test_accounts_login(self):
        r = self.client.get(reverse("account_login"), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(
            r, '<input type="submit" class="button" value="Sign In" />', html=True
        )


class TestTemplateAdmin(TestOrganizationMixin, TestCase):
    def test_org_admin_create_shareable_template(self):
        administrator = self._create_administrator()
        self.client.force_login(administrator)
        response = self.client.post(
            reverse("admin:testapp_template_add"),
            data={
                "name": "test-template",
                "organization": "",
            },
            follow=True,
        )
        self.assertContains(
            response,
            '<ul class="errorlist" id="id_organization_error">'
            "<li>This field is required.</li></ul>",
        )
        self.assertEqual(Template.objects.count(), 0)

    def test_superuser_create_shareable_template(self):
        admin = self._create_admin()
        self.client.force_login(admin)
        response = self.client.post(
            reverse("admin:testapp_template_add"),
            data={
                "name": "test-template",
                "organization": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Template.objects.count(), 1)
