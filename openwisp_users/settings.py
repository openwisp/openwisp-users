from django.conf import settings
from openwisp_utils.utils import default_or_test

ORGANIZATION_USER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATION_USER_ADMIN', False)
ORGANIZATION_OWNER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATION_OWNER_ADMIN', True)
USERS_AUTH_API = getattr(settings, 'OPENWISP_USERS_AUTH_API', True)
USERS_AUTH_THROTTLE_RATE = getattr(
    settings,
    'OPENWISP_USERS_AUTH_THROTTLE_RATE',
    default_or_test(value='20/day', test=None),
)
AUTH_BACKEND_AUTO_PREFIXES = getattr(
    settings, 'OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES', tuple()
)
# Set the AutocompleteFilter view if it is not defined in the settings
setattr(
    settings,
    'OPENWISP_AUTOCOMPLETE_FILTER_VIEW',
    getattr(
        settings,
        'OPENWISP_AUTOCOMPLETE_FILTER_VIEW',
        'openwisp_users.views.AutocompleteJsonView',
    ),
)
