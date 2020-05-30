from openwisp_users.tests.test_admin import (
    TestBasicUsersIntegration as BaseTestBasicUsersIntegration,
)
from openwisp_users.tests.test_admin import (
    TestMultitenantAdmin as BaseTestMultitenantAdmin,
)
from openwisp_users.tests.test_admin import TestUsersAdmin as BaseTestUsersAdmin
from openwisp_users.tests.test_api.test_authentication import (
    AuthenticationTests as BaseAuthenticationTests,
)
from openwisp_users.tests.test_api.test_throttling import (
    RatelimitTests as BaseRatelimitTests,
)
from openwisp_users.tests.test_api.test_views import (
    TestRestFrameworkViews as BaseTestRestFrameworkViews,
)
from openwisp_users.tests.test_models import TestUsers as BaseTestUsers

additional_fields = [
    ('social_security_number', '123-45-6789'),
    ('details', 'Example value for detail used during testing.'),
]


class TestUsersAdmin(BaseTestUsersAdmin):
    app_label = 'sample_users'
    _additional_user_fields = additional_fields

    # def _get_edit_form_inline_params(self, user, organization):
    #     """
    #     This function is created to be overridden
    #     when the user extends openwisp-users
    #     and adds inline forms in the User model
    #     """
    #     add your code here


class TestBasicUsersIntegration(BaseTestBasicUsersIntegration):
    app_label = 'sample_users'
    _additional_user_fields = additional_fields


class TestMultitenantAdmin(BaseTestMultitenantAdmin):
    app_label = 'sample_users'


class TestUsers(BaseTestUsers):
    pass


class AuthenticationTests(BaseAuthenticationTests):
    pass


class TestRestFrameworkViews(BaseTestRestFrameworkViews):
    pass


class RatelimitTests(BaseRatelimitTests):
    pass


del BaseTestUsersAdmin
del BaseTestBasicUsersIntegration
del BaseTestMultitenantAdmin
del BaseTestUsers
del BaseAuthenticationTests
del BaseRatelimitTests
del BaseTestRestFrameworkViews
