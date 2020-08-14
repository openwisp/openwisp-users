from django.conf import settings
from openwisp_utils.utils import default_or_test

ORGANIZATON_USER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_USER_ADMIN', False)
ORGANIZATON_OWNER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', True)
USERS_AUTH_API = getattr(settings, 'OPENWISP_USERS_AUTH_API', False)
USERS_AUTH_THROTTLE_RATE = getattr(
    settings,
    'OPENWISP_USERS_AUTH_THROTTLE_RATE',
    default_or_test(value='20/day', test=None),
)
