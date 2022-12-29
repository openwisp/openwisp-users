from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db.models import Q
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from swapper import load_model

from .mixins import SeleniumTestMixin, TestMultitenancyMixin

Organization = load_model('openwisp_users', 'Organization')


class TestOrganizationAutocompleteField(
    SeleniumTestMixin, TestMultitenancyMixin, StaticLiveServerTestCase
):
    admin_username = 'admin'
    admin_password = 'password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = webdriver.ChromeOptions()
        if getattr(settings, 'SELENIUM_HEADLESS', True):
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--remote-debugging-port=9222')
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
        cls.web_driver = webdriver.Chrome(
            options=chrome_options, desired_capabilities=capabilities
        )

    @classmethod
    def tearDownClass(cls):
        cls.web_driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.admin = self._create_admin(
            username=self.admin_username, password=self.admin_password
        )

    def _test_multitenant_autocomplete_org_field(
        self, username, password, path, visible, hidden
    ):
        self.login(username=username, password=password)
        self.open(path)
        self.web_driver.find_element_by_css_selector(
            '#select2-id_organization-container'
        ).click()
        WebDriverWait(self.web_driver, 2).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, '.select2-results__option.loading-results')
            )
        )
        options = self.web_driver.find_elements_by_css_selector(
            '.select2-results__option'
        )
        for option in options:
            self.assertIn(option.text, visible)
            self.assertNotIn(option.text, hidden)

    def test_book_add_form_organization_field(self):
        path = reverse('admin:testapp_book_add')
        org1 = self._create_org(name='org1')
        org2 = self._create_org(name='org2')
        administrator = self._create_administrator(
            organizations=[org1], username='tester', password='tester'
        )
        administrator.user_permissions.add(
            *Permission.objects.filter(
                Q(codename__contains='shelf') | Q(codename='view_organization')
            ).values_list('id', flat=True),
        )

        with self.subTest('Test superuser'):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username=self.admin_username,
                password=self.admin_password,
                visible=Organization.objects.values_list('name', flat=True),
                hidden=[],
            )
        self.open(reverse('admin:logout'))

        with self.subTest('Test organization user: 1 org'):

            self._test_multitenant_autocomplete_org_field(
                path=path,
                username='tester',
                password='tester',
                visible=[org1.name],
                hidden=Organization.objects.exclude(id=org1.id).values_list(
                    'name', flat=True
                ),
            )
            org_select = Select(
                self.web_driver.find_element_by_css_selector('#id_organization')
            )
            self.assertEqual(len(org_select.all_selected_options), 1)
            self.assertEqual(org_select.first_selected_option.text, org1.name)
        self.open(reverse('admin:logout'))

        with self.subTest('Test organization user: 2 orgs'):
            self._create_org_user(user=administrator, organization=org2, is_admin=True)

            self._test_multitenant_autocomplete_org_field(
                path=path,
                username='tester',
                password='tester',
                visible=[org1.name, org2.name],
                hidden=Organization.objects.exclude(
                    id__in=[org1.id, org2.id]
                ).values_list('name', flat=True),
            )
            org_select = Select(
                self.web_driver.find_element_by_css_selector('#id_organization')
            )
            self.assertEqual(len(org_select.all_selected_options), 0)
        self.open(reverse('admin:logout'))

    def test_shelf_add_form_organization_field(self):
        path = reverse('admin:testapp_shelf_add')
        org1 = self._create_org(name='org1')
        administrator = self._create_administrator(
            organizations=[org1], username='tester', password='tester'
        )
        administrator.user_permissions.add(
            *Permission.objects.filter(
                Q(codename__contains='shelf') | Q(codename='view_organization')
            ).values_list('id', flat=True),
        )

        with self.subTest('Test superuser'):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username=self.admin_username,
                password=self.admin_password,
                visible=list(Organization.objects.values_list('name', flat=True))
                + ['Shared systemwide (no organization)'],
                hidden=[],
            )
        self.open(reverse('admin:logout'))

        with self.subTest('Test organization user'):
            self._test_multitenant_autocomplete_org_field(
                path=path,
                username='tester',
                password='tester',
                visible=[org1.name],
                hidden=list(
                    Organization.objects.exclude(id=org1.id).values_list(
                        'name', flat=True
                    )
                )
                + ['Shared systemwide (no organization)'],
            )
            org_select = Select(
                self.web_driver.find_element_by_css_selector('#id_organization')
            )
            self.assertEqual(len(org_select.all_selected_options), 1)
            self.assertEqual(org_select.first_selected_option.text, org1.name)
        self.open(reverse('admin:logout'))
