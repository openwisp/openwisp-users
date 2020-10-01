from django.conf import settings
from openwisp_utils.utils import default_or_test

ORGANIZATION_USER_ADMIN = (
    # setting with typographic error for maintaining backward compatibility
    # TODO: remove in openwisp-users 0.5
    getattr(settings, 'OPENWISP_ORGANIZATON_USER_ADMIN', False) or
    getattr(settings, 'OPENWISP_ORGANIZATION_USER_ADMIN', False)
)
ORGANIZATION_OWNER_ADMIN = (
    # setting with typographic error for maintaining backward compatibility
    # TODO: remove in openwisp-users 0.5
    getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', True) or
    getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', True)
)
USERS_AUTH_API = getattr(settings, 'OPENWISP_USERS_AUTH_API', False)
USERS_AUTH_THROTTLE_RATE = getattr(
    settings,
    'OPENWISP_USERS_AUTH_THROTTLE_RATE',
    default_or_test(value='20/day', test=None),
)
