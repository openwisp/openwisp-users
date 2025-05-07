from openwisp_users.tests.test_api import AuthenticationMixin, TestMultitenantApiMixin

from .. import CreateMixin


class TestMultitenancyMixin(CreateMixin, TestMultitenantApiMixin, AuthenticationMixin):
    pass
