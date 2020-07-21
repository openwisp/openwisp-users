from openwisp_users.tests.test_api import AuthenticationMixin
from openwisp_users.tests.utils import TestMultitenantAdminMixin, TestOrganizationMixin

from .. import CreateMixin


class TestMultitenancyMixin(
    CreateMixin, TestMultitenantAdminMixin, AuthenticationMixin, TestOrganizationMixin
):
    pass
