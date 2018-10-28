from django.conf import settings


ORGANIZATON_OWNER_ADMIN = getattr(settings, 'OPENWISP_ORGANIZATON_OWNER_ADMIN', False)
