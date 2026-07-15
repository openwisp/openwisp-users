from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from openwisp_users.multitenancy import MultitenantAdminMixin

from ..admin import LibraryParentAdmin, ShelfAdmin
from ..models import Book, Library, Shelf
from .mixins import TestMultitenancyMixin

User = get_user_model()


class ShelfDisabledOrgWriteAllowedAdmin(MultitenantAdminMixin, admin.ModelAdmin):
    # dedicated admin used only to test the disabled_organization_write_protection
    # opt-out; kept separate from ShelfAdmin so its default (protected)
    # behaviour stays covered by the other tests in this file
    disabled_organization_write_protection = False
    fields = ["name", "organization"]


class TestMultitenancy(TestMultitenancyMixin, TestCase):
    book_model = Book
    shelf_model = Shelf

    def _create_multitenancy_test_env(self):
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        inactive = self._create_org(name="inactive-org", is_active=False)
        operator = self._create_operator(
            organizations=[org1, inactive],
        )
        administrator = self._create_administrator(
            organizations=[org1, inactive],
        )
        s1 = self._create_shelf(name="shell1", organization=org1)
        s2 = self._create_shelf(name="shell2", organization=org2)
        s3 = self._create_shelf(name="shell3", organization=inactive)
        b1 = self._create_book(name="book1", organization=org1, shelf=s1)
        b2 = self._create_book(name="book2", organization=org2, shelf=s2)
        b3 = self._create_book(name="book3", organization=inactive, shelf=s3)
        data = dict(
            s1=s1,
            s2=s2,
            s3_inactive=s3,
            b1=b1,
            b2=b2,
            b3_inactive=b3,
            org1=org1,
            org2=org2,
            inactive=inactive,
            operator=operator,
            administrator=administrator,
        )
        return data

    def test_shelf_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse("admin:testapp_shelf_changelist"),
            visible=[data["s1"].name, data["org1"].name],
            hidden=[data["s2"].name, data["org2"].name, data["s3_inactive"].name],
            administrator=True,
        )

    def test_book_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse("admin:testapp_book_changelist"),
            visible=[data["b1"].name, data["org1"].name],
            hidden=[data["b2"].name, data["org2"].name, data["b3_inactive"].name],
            administrator=True,
        )

    def test_book_shelf_fk_queryset(self):
        data = self._create_multitenancy_test_env()
        self._test_multitenant_admin(
            url=reverse("admin:testapp_book_add"),
            visible=[data["s1"].name],
            hidden=[data["s2"].name, data["s3_inactive"].name],
            select_widget=True,
            administrator=True,
        )

    def test_shelf_disabled_organization_admin_guard(self):
        org = self._get_org()
        shelf = self._create_shelf(name="disable-guard-shelf", organization=org)
        self.client.force_login(self._get_admin())
        org.is_active = False
        org.save()
        change_path = reverse("admin:testapp_shelf_change", args=[shelf.pk])
        delete_path = reverse("admin:testapp_shelf_delete", args=[shelf.pk])

        with self.subTest("change blocked for superuser"):
            # has_view_permission is untouched, so the read-only form
            # still renders with a 200; has_change_permission is checked
            # before form validation on POST, so it 403s regardless of
            # what other field values are (or aren't) submitted
            r = self.client.get(change_path)
            self.assertEqual(r.status_code, 200)
            r = self.client.post(
                change_path, {"name": "renamed-shelf", "organization": str(org.pk)}
            )
            self.assertEqual(r.status_code, 403)
            shelf.refresh_from_db()
            self.assertEqual(shelf.name, "disable-guard-shelf")

        with self.subTest("delete still allowed"):
            r = self.client.post(delete_path, {"post": "yes"}, follow=True)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(self.shelf_model.objects.filter(pk=shelf.pk).count(), 0)

    def test_multitenant_parent_disabled_organization_guard(self):
        data = self._create_multitenancy_test_env()
        library_admin = LibraryParentAdmin(Library, admin.site)
        request = RequestFactory().get("/")
        request.user = self._get_admin()
        active_library = Library.objects.create(name="lib-active", book=data["b1"])
        disabled_library = Library.objects.create(
            name="lib-disabled", book=data["b3_inactive"]
        )

        with self.subTest("change allowed for object of active parent org"):
            self.assertEqual(
                library_admin.has_change_permission(request, active_library), True
            )

        with self.subTest("change blocked for object of disabled parent org"):
            # applies to superusers too: the object is reached through
            # multitenant_parent, so the guard must traverse it
            self.assertEqual(
                library_admin.has_change_permission(request, disabled_library), False
            )

        with self.subTest("delete still allowed for object of disabled parent org"):
            self.assertEqual(
                library_admin.has_delete_permission(request, disabled_library), True
            )

    def test_add_permission_hidden_without_active_managed_org(self):
        disabled_org = self._create_org(name="operator-disabled-org", is_active=False)
        active_org = self._create_org(name="operator-active-org")
        operator = self._create_operator()
        operator.user_permissions.add(Permission.objects.get(codename="add_shelf"))
        shelf_admin = ShelfAdmin(Shelf, admin.site)
        request = RequestFactory().get("/")

        with self.subTest("no active managed org hides the Add button"):
            self._create_org_user(
                user=operator, organization=disabled_org, is_admin=True
            )
            request.user = User.objects.get(pk=operator.pk)
            self.assertEqual(shelf_admin.has_add_permission(request), False)

        with self.subTest("an active managed org restores the Add button"):
            self._create_org_user(user=operator, organization=active_org, is_admin=True)
            request.user = User.objects.get(pk=operator.pk)
            self.assertEqual(shelf_admin.has_add_permission(request), True)

    def test_disabled_organization_write_protection_opt_out(self):
        org = self._get_org()
        shelf = self._create_shelf(name="opt-out-shelf", organization=org)
        org.is_active = False
        org.save()
        shelf_admin = ShelfDisabledOrgWriteAllowedAdmin(Shelf, admin.site)
        request = RequestFactory().get("/")
        request.user = self._get_admin()

        with self.subTest("change permission is not blocked for the opted-out admin"):
            self.assertEqual(shelf_admin.has_change_permission(request, shelf), True)

        with self.subTest("the disabled organization stays in the field's choices"):
            form_class = shelf_admin.get_form(request, shelf)
            org_field = form_class.base_fields["organization"]
            self.assertIn(org.pk, org_field.queryset.values_list("pk", flat=True))

        with self.subTest("the form can still be saved"):
            form_class = shelf_admin.get_form(request, shelf)
            form = form_class(
                data={"name": shelf.name, "organization": org.pk}, instance=shelf
            )
            self.assertTrue(form.is_valid(), form.errors)
            form.save()
            shelf.refresh_from_db()
            self.assertEqual(shelf.organization_id, org.pk)
