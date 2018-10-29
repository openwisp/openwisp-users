from django.conf import settings

ORGANIZATON_USER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_USER_ADMIN', False)
ORGANIZATON_OWNER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', False)
