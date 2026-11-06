from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.test import RequestFactory
from django.test.utils import isolate_apps
from django.urls import reverse
from swapper import load_model

from openwisp_users.admin import OrganizationAdmin, OrganizationUserInline
from openwisp_users.tests.test_accounts import TestAccountView as BaseTestAccountView
from openwisp_users.tests.test_admin import (
    TestBasicUsersIntegration as BaseTestBasicUsersIntegration,
)
from openwisp_users.tests.test_admin import (
    TestMultitenantAdmin as BaseTestMultitenantAdmin,
)
from openwisp_users.tests.test_admin import (
    TestUserPasswordExpiration as BaseTestUserPasswordExpiration,
)
from openwisp_users.tests.test_admin import TestUsersAdmin as BaseTestUsersAdmin
from openwisp_users.tests.test_api.test_api import TestUsersApi as BaseTestUsersApi
from openwisp_users.tests.test_api.test_authentication import (
    AuthenticationTests as BaseAuthenticationTests,
)
from openwisp_users.tests.test_api.test_password_reset import (
    TestPasswordChangeAPI as BaseTestPasswordChangeAPI,
)
from openwisp_users.tests.test_api.test_password_reset import (
    TestPasswordResetAPI as BaseTestPasswordResetAPI,
)
from openwisp_users.tests.test_api.test_throttling import (
    RatelimitTests as BaseRatelimitTests,
)
from openwisp_users.tests.test_api.test_views import (
    TestRestFrameworkViews as BaseTestRestFrameworkViews,
)
from openwisp_users.tests.test_backends import TestBackends as BaseTestBackends
from openwisp_users.tests.test_middlewares import (
    TestPasswordExpirationMiddleware as BaseTestPasswordExpirationMiddleware,
)
from openwisp_users.tests.test_models import TestUsers as BaseTestUsers

from .models import Group, Organization, OrganizationInlineModel

additional_fields = [
    ("social_security_number", "123-45-6789"),
    ("details", "Example value for detail used during testing."),
]


class GetEditFormInlineMixin(object):
    """
    The following code is only used in testing,
    please remove it or replace it with your
    Inline form fields data.
    """

    def _get_org_edit_form_inline_params(self, user, organization):
        """
        This function is created to be overridden
        when the user extends openwisp-users
        and adds inline forms in the Organization model.
        """
        params = super()._get_user_edit_form_inline_params(user, organization)
        params.update(
            {
                "organizationinlinemodel-TOTAL_FORMS": 1,
                "organizationinlinemodel-INITIAL_FORMS": 0,
                "organizationinlinemodel-MIN_NUM_FORMS": 0,
                "organizationinlinemodel-MAX_NUM_FORMS": 1,
                "organizationinlinemodel-0-details": "",
                "organizationinlinemodel-0-user": str(organization.pk),
            }
        )
        return params

    def _get_user_edit_form_inline_params(self, user, organization):
        """
        This function is created to be overridden
        when the user extends openwisp-users
        and adds inline forms in the User model.
        """
        params = super()._get_user_edit_form_inline_params(user, organization)
        params.update(
            {
                "userinlinemodel-TOTAL_FORMS": 1,
                "userinlinemodel-INITIAL_FORMS": 0,
                "userinlinemodel-MIN_NUM_FORMS": 0,
                "userinlinemodel-MAX_NUM_FORMS": 1,
                "userinlinemodel-0-details": "",
                "userinlinemodel-0-user": str(user.pk),
            }
        )
        return params


class TestUsersAdmin(GetEditFormInlineMixin, BaseTestUsersAdmin):
    app_label = "sample_users"
    _additional_user_fields = additional_fields

    def test_disabled_organization_inline_rejects_posted_changes(self):
        """The sample adds an organization inline without multitenancy protection.

        Verify the parent admin blocks forged add and change requests for that
        inline when the organization is disabled.
        """
        self.client.force_login(self._get_admin())
        for existing in (False, True):
            with self.subTest(existing=existing):
                organization = self._create_org(
                    name=f"disabled-inline-{existing}", is_active=False
                )
                if existing:
                    row = OrganizationInlineModel.objects.create(
                        organization=organization, details="original"
                    )
                data = {
                    "is_active": "",
                    "owner-TOTAL_FORMS": "0",
                    "owner-INITIAL_FORMS": "0",
                    "organizationinlinemodel-TOTAL_FORMS": "1",
                    "organizationinlinemodel-INITIAL_FORMS": str(int(existing)),
                    "organizationinlinemodel-0-organization": str(organization.pk),
                    "organizationinlinemodel-0-details": "tampered",
                }
                if existing:
                    data["organizationinlinemodel-0-id"] = str(row.pk)
                response = self.client.post(
                    reverse(
                        "admin:sample_users_organization_change", args=[organization.pk]
                    ),
                    data,
                )
                self.assertEqual(response.status_code, 302)
                rows = OrganizationInlineModel.objects.filter(organization=organization)
                self.assertEqual(rows.count(), int(existing))
                if existing:
                    row.refresh_from_db()
                    self.assertEqual(row.details, "original")
                organization.refresh_from_db()
                self.assertFalse(organization.is_active)

    def test_disabling_organization_blocks_inline_changes(self):
        """The sample adds an inline without its own write protection.

        Verify the parent blocks inline additions and changes in the same
        request that disables the organization, while allowing deletion.
        """
        self.client.force_login(self._get_admin())
        for operation in ("add", "change", "delete"):
            with self.subTest(operation=operation):
                existing = operation != "add"
                organization = self._create_org(name=f"disable-with-inline-{operation}")
                if existing:
                    row = OrganizationInlineModel.objects.create(
                        organization=organization, details="original"
                    )
                data = {
                    "name": organization.name,
                    "slug": organization.slug,
                    "owner-TOTAL_FORMS": "0",
                    "owner-INITIAL_FORMS": "0",
                    "organizationinlinemodel-TOTAL_FORMS": "1",
                    "organizationinlinemodel-INITIAL_FORMS": str(int(existing)),
                    "organizationinlinemodel-0-organization": str(organization.pk),
                    "organizationinlinemodel-0-details": "tampered",
                }
                if existing:
                    data["organizationinlinemodel-0-id"] = str(row.pk)
                if operation == "delete":
                    data["organizationinlinemodel-0-DELETE"] = "on"
                response = self.client.post(
                    reverse(
                        "admin:sample_users_organization_change", args=[organization.pk]
                    ),
                    data,
                )
                self.assertEqual(response.status_code, 302)
                organization.refresh_from_db()
                self.assertFalse(organization.is_active)
                rows = OrganizationInlineModel.objects.filter(organization=organization)
                self.assertEqual(rows.count(), int(operation == "change"))
                if operation == "change":
                    row.refresh_from_db()
                    self.assertEqual(row.details, "original")

    def test_disabled_membership_inline_protects_extension_field(self):
        """A downstream inline may expose fields added to the membership model.

        The sample's swapped membership adds ``details``; verify a forged change
        to that field is ignored when its organization is disabled.
        """

        class ExtendedMembershipInline(OrganizationUserInline):
            fields = (*OrganizationUserInline.fields, "details")

        organization = self._create_org(name="extended-membership-inline")
        user = self._create_user()
        membership = self._create_org_user(
            organization=organization, user=user, details="original"
        )
        organization.is_active = False
        organization.save()
        request = RequestFactory().post(
            reverse("admin:sample_users_user_change", args=[user.pk])
        )
        request.user = self._get_admin()
        inline = ExtendedMembershipInline(type(user), admin.site)
        formset = inline.get_formset(request, user)(
            instance=user,
            prefix="memberships",
            data={
                "memberships-TOTAL_FORMS": "1",
                "memberships-INITIAL_FORMS": "1",
                "memberships-0-id": str(membership.pk),
                "memberships-0-user": str(user.pk),
                "memberships-0-organization": str(organization.pk),
                "memberships-0-details": "tampered",
            },
        )
        self.assertTrue(formset.forms[0].fields["details"].disabled)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        membership.refresh_from_db()
        self.assertEqual(membership.details, "original")

    @isolate_apps("openwisp2.sample_users")
    def test_disabled_organization_m2m_field_is_readonly(self):
        """An extended organization can add editable many-to-many fields.

        Use an isolated subclass of the sample model to verify those fields are
        read-only when disabled, while the organization can still be re-enabled.
        """

        class ExtendedOrganization(Organization):
            groups = models.ManyToManyField(Group, blank=True)

            class Meta:
                app_label = "sample_users"

        organization = ExtendedOrganization(is_active=False)
        request = RequestFactory().get(reverse("admin:sample_users_organization_add"))
        request.user = self._get_admin()
        model_admin = OrganizationAdmin(ExtendedOrganization, admin.site)
        for active in (True, False):
            with self.subTest(active=active):
                organization.is_active = active
                form = model_admin.get_form(
                    request, organization, fields=("is_active", "groups")
                )
                self.assertEqual("groups" in form.base_fields, active)
                self.assertIn("is_active", form.base_fields)


class TestUserPasswordExpiration(BaseTestUserPasswordExpiration):
    pass


class TestBasicUsersIntegration(GetEditFormInlineMixin, BaseTestBasicUsersIntegration):
    app_label = "sample_users"
    _additional_user_fields = additional_fields

    def test_login_page(self):
        super().test_login_page()
        # Verify that the sample app's override template is used
        r = self.client.get(reverse("admin:login"))
        self.assertContains(r, "<p>Sample Login Template</p>")

    def test_action_confirmation_template(self):
        super().test_action_confirmation_template()
        # Verify that the sample app's override template is used
        users = get_user_model().objects.filter(is_superuser=False)
        url = reverse(f"admin:{self.app_label}_user_changelist")
        data = {
            "action": "make_active",
            "_selected_action": [str(u.pk) for u in users],
        }
        response = self.client.post(url, data)
        self.assertContains(response, "<p>Sample Action Confirmation Template</p>")


class TestMultitenantAdmin(BaseTestMultitenantAdmin):
    app_label = "sample_users"


class TestUsers(BaseTestUsers):
    def test_add_user_preserves_extension_field(self):
        """The sample membership adds ``details`` to the built-in fields.

        Verify the organization's public ``add_user`` method saves values for
        fields added by downstream membership models.
        """
        organization = self._create_org(name="extended-add-user")
        membership = organization.add_user(self._create_user(), details="original")
        membership.refresh_from_db()
        self.assertEqual(membership.details, "original")

    def test_disabled_membership_rejects_extension_field_change(self):
        """Membership validation must cover fields added by downstream models.

        The sample's swapped membership adds ``details``; changing it must fail
        validation after the organization is disabled.
        """
        organization = self._create_org(name="extended-membership")
        membership = self._create_org_user(
            organization=organization, details="original"
        )
        organization.is_active = False
        organization.save()
        membership.full_clean()
        membership.details = "changed"
        with self.assertRaisesMessage(
            ValidationError,
            "Memberships of a disabled organization cannot be modified.",
        ):
            membership.full_clean()
        membership.refresh_from_db()
        self.assertEqual(membership.details, "original")

    def test_disabled_owner_rejects_extended_field_change(self):
        organization = self._create_org(name="extended-owner")
        user = self._create_user()
        membership = self._create_org_user(organization=organization, user=user)
        owner = self._create_org_owner(
            organization=organization, organization_user=membership
        )
        organization.is_active = False
        organization.save()
        owner.full_clean()
        owner.details = "changed"
        with self.assertRaises(ValidationError):
            owner.full_clean()
        owner.delete()
        owner_model = load_model("openwisp_users", "OrganizationOwner")
        self.assertEqual(
            owner_model.objects.filter(organization=organization).count(), 0
        )


class AuthenticationTests(BaseAuthenticationTests):
    pass


class TestRestFrameworkViews(BaseTestRestFrameworkViews):
    pass


class RatelimitTests(BaseRatelimitTests):
    pass


class TestBackends(BaseTestBackends):
    pass


class TestAccountView(BaseTestAccountView):
    pass


class TestUsersApi(BaseTestUsersApi):
    pass


class TestPasswordExpirationMiddleware(BaseTestPasswordExpirationMiddleware):
    pass


class TestPasswordResetAPI(BaseTestPasswordResetAPI):
    pass


class TestPasswordChangeAPI(BaseTestPasswordChangeAPI):
    pass


del BaseTestUsersAdmin
del BaseTestUserPasswordExpiration
del BaseTestBasicUsersIntegration
del BaseTestMultitenantAdmin
del BaseTestUsers
del BaseAuthenticationTests
del BaseRatelimitTests
del BaseTestRestFrameworkViews
del BaseTestBackends
del BaseTestUsersApi
del BaseTestAccountView
del BaseTestPasswordExpirationMiddleware
del BaseTestPasswordResetAPI
del BaseTestPasswordChangeAPI
