from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db.models import Q
from django.test import tag
from django.urls import reverse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from swapper import load_model

from openwisp_utils.test_selenium_mixins import SeleniumTestMixin

from .mixins import TestMultitenancyMixin

Organization = load_model("openwisp_users", "Organization")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
User = get_user_model()


@tag("selenium_tests")
class TestOrganizationAutocompleteField(
    SeleniumTestMixin, TestMultitenancyMixin, StaticLiveServerTestCase
):
    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def logout(self, driver=None):
        super().logout(driver)
        driver = driver or self.web_driver
        try:
            WebDriverWait(driver, 5).until(
                EC.url_to_be(f"{self.live_server_url}{reverse('admin:logout')}")
            )
        except TimeoutException:
            self.fail(
                "Browser failed to logout the user: URL did not change to logout page"
            )

    def _test_multitenant_autocomplete_org_field(
        self, username, password, path, visible, hidden
    ):
        self.login(username=username, password=password)
        self.open(path)
        self.find_element(By.CSS_SELECTOR, "#select2-id_organization-container").click()
        WebDriverWait(self.web_driver, 2).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".select2-results__option.loading-results")
            )
        )
        options = self.find_elements(By.CSS_SELECTOR, ".select2-results__option")
        for option in options:
            self.assertIn(option.text, visible)
            self.assertNotIn(option.text, hidden)

    def test_book_add_form_organization_field(self):
        path = reverse("admin:testapp_book_add")
        org1 = self._create_org(name="org1")
        org2 = self._create_org(name="org2")
        disabled_org = self._create_org(name="disabled-org", is_active=False)
        administrator = self._create_administrator(
            organizations=[org1], username="tester", password="tester"
        )
        administrator.user_permissions.add(
            *Permission.objects.filter(
                Q(codename__contains="shelf")
                | Q(codename="view_organization")
                | Q(codename__contains="book")
            ).values_list("id", flat=True),
        )

        with self.subTest("Test superuser"):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username=self.admin_username,
                password=self.admin_password,
                visible=Organization.objects.exclude(id=disabled_org.id).values_list(
                    "name", flat=True
                ),
                hidden=[disabled_org.name],
            )
        self.logout()

        with self.subTest("Test organization user: 1 org"):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username="tester",
                password="tester",
                visible=[org1.name],
                hidden=Organization.objects.exclude(id=org1.id).values_list(
                    "name", flat=True
                ),
            )
            org_select = Select(self.find_element(By.CSS_SELECTOR, "#id_organization"))
            self.assertEqual(len(org_select.all_selected_options), 1)
            self.assertEqual(org_select.first_selected_option.text, org1.name)
        self.logout()

        with self.subTest("Test organization user: 2 orgs"):
            self._create_org_user(user=administrator, organization=org2, is_admin=True)

            self._test_multitenant_autocomplete_org_field(
                path=path,
                username="tester",
                password="tester",
                visible=[org1.name, org2.name],
                hidden=Organization.objects.exclude(
                    id__in=[org1.id, org2.id]
                ).values_list("name", flat=True),
            )
            org_select = Select(self.find_element(By.CSS_SELECTOR, "#id_organization"))
            self.assertEqual(len(org_select.all_selected_options), 0)
        self.logout()

    def test_shelf_add_form_organization_field(self):
        path = reverse("admin:testapp_shelf_add")
        org1 = self._create_org(name="org1")
        administrator = self._create_administrator(
            organizations=[org1], username="tester", password="tester"
        )
        administrator.user_permissions.add(
            *Permission.objects.filter(
                Q(codename__contains="shelf") | Q(codename="view_organization")
            ).values_list("id", flat=True),
        )

        with self.subTest("Test superuser"):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username=self.admin_username,
                password=self.admin_password,
                visible=list(Organization.objects.values_list("name", flat=True))
                + ["Shared systemwide (no organization)"],
                hidden=[],
            )
        self.logout()

        with self.subTest("Test organization user"):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username="tester",
                password="tester",
                visible=[org1.name],
                hidden=list(
                    Organization.objects.exclude(id=org1.id).values_list(
                        "name", flat=True
                    )
                )
                + ["Shared systemwide (no organization)"],
            )
            org_select = Select(self.find_element(By.CSS_SELECTOR, "#id_organization"))
            self.assertEqual(len(org_select.all_selected_options), 1)
            self.assertEqual(org_select.first_selected_option.text, org1.name)
        self.logout()

    def test_user_add_form_does_not_hang(self):
        path = reverse(f"admin:{User._meta.app_label}_user_add")
        self.login(username=self.admin_username, password=self.admin_password)
        self.open(path)
        WebDriverWait(self.web_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select[id$='-organization'] + span.select2")
            )
        )
        self.logout()

    def test_dynamic_organization_inline_normalizes_shared_value_on_submit(self):
        # OrganizationUser.organization is a required field, so selecting
        # "Shared systemwide (no organization)" on an inline row must be
        # rejected with a validation error rather than saved as None.
        path = reverse(f"admin:{User._meta.app_label}_user_add")
        username = "shared-inline-user"
        self.login(username=self.admin_username, password=self.admin_password)
        self.open(path)
        self.find_element(
            By.CSS_SELECTOR, "#openwisp_users_organizationuser-0 .inline-deletelink"
        ).click()
        self.find_element(
            By.CSS_SELECTOR, "#openwisp_users_organizationuser-group .add-row a"
        ).click()
        org_field = WebDriverWait(self.web_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#id_openwisp_users_organizationuser-0-organization")
            )
        )
        self.web_driver.execute_script(
            "arguments[0].value = 'null'; "
            "django.jQuery(arguments[0]).trigger('change');",
            org_field,
        )
        self.find_element(By.ID, "id_username").send_keys(username)
        self.find_element(By.ID, "id_email").send_keys("test@openwisp.org")
        self.find_element(By.ID, "id_password1").send_keys("testpassword")
        self.find_element(By.ID, "id_password2").send_keys("testpassword")
        self.find_element(By.CSS_SELECTOR, "input[name='_save']").click()
        error = WebDriverWait(self.web_driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#openwisp_users_organizationuser-0 .errorlist")
            )
        )
        self.assertIn("This field is required", error.text)
        self.assertFalse(
            OrganizationUser.objects.filter(user__username=username).exists()
        )
        self.logout()
