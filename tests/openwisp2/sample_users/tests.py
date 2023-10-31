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
from openwisp_users.tests.test_api.test_throttling import (
    RatelimitTests as BaseRatelimitTests,
)
from openwisp_users.tests.test_api.test_views import (
    TestRestFrameworkViews as BaseTestRestFrameworkViews,
)
from openwisp_users.tests.test_backends import TestBackends as BaseTestBackends
from openwisp_users.tests.test_models import TestUsers as BaseTestUsers

additional_fields = [
    ('social_security_number', '123-45-6789'),
    ('details', 'Example value for detail used during testing.'),
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
                'organizationinlinemodel-TOTAL_FORMS': 1,
                'organizationinlinemodel-INITIAL_FORMS': 0,
                'organizationinlinemodel-MIN_NUM_FORMS': 0,
                'organizationinlinemodel-MAX_NUM_FORMS': 1,
                'organizationinlinemodel-0-details': '',
                'organizationinlinemodel-0-user': str(organization.pk),
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
                'userinlinemodel-TOTAL_FORMS': 1,
                'userinlinemodel-INITIAL_FORMS': 0,
                'userinlinemodel-MIN_NUM_FORMS': 0,
                'userinlinemodel-MAX_NUM_FORMS': 1,
                'userinlinemodel-0-details': '',
                'userinlinemodel-0-user': str(user.pk),
            }
        )
        return params


class TestUsersAdmin(GetEditFormInlineMixin, BaseTestUsersAdmin):
    app_label = 'sample_users'
    _additional_user_fields = additional_fields


class TestUserPasswordExpiration(BaseTestUserPasswordExpiration):
    pass


class TestBasicUsersIntegration(GetEditFormInlineMixin, BaseTestBasicUsersIntegration):
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


class TestBackends(BaseTestBackends):
    pass


class TestAccountView(BaseTestAccountView):
    pass


class TestUsersApi(BaseTestUsersApi):
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
