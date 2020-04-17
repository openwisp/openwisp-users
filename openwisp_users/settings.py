from django.conf import settings

ORGANIZATON_USER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_USER_ADMIN', False)
ORGANIZATON_OWNER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', False)
USERS_AUTH_API = getattr(settings, 'OPENWISP_USERS_AUTH_API', False)
USERS_AUTH_THROTTLE_RATE = getattr(
    settings, 'OPENWISP_USERS_AUTH_THROTTLE_RATE', '20/day'
)
