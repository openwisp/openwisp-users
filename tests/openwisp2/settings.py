import os
import sys

from celery.schedules import crontab

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TESTING = sys.argv[1] == 'test'
PARALLEL = '--parallel' in sys.argv
SHELL = 'shell' in sys.argv or 'shell_plus' in sys.argv
SAMPLE_APP = os.environ.get('SAMPLE_APP', False)

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'openwisp-users.db'
        if not SAMPLE_APP
        else 'openwisp-users-SAMPLE_APP.db',
    }
}

SECRET_KEY = 'fn)t*+$)ugeyip6-#txyy$5wf2ervc0d2n#h)qb)y5@ly$t*@w'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # overrides some templates in django-allauth
    'openwisp_users.accounts',
    'django_extensions',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'openwisp_users',
    # openwisp2 admin theme
    # (must be loaded here)
    'openwisp_utils.admin_theme',
    # must come before the django admin
    # to override the admin login page
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.admin',
    'admin_auto_filters',
    'django.contrib.sites',
    'drf_yasg',
    'testapp',
    'reversion',
    'django_filters',
]

AUTH_USER_MODEL = 'openwisp_users.User'
SITE_ID = 1

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openwisp_utils.staticfiles.DependencyFinder',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'openwisp_users.middleware.PasswordExpirationMiddleware',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'openwisp_users.password_validation.PasswordReuseValidator'}
]

ROOT_URLCONF = 'openwisp2.urls'

TIME_ZONE = 'Europe/Rome'
LANGUAGE_CODE = 'en-gb'
USE_TZ = True
USE_I18N = False
USE_L10N = False
STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(BASE_DIR), 'openwisp_users', 'templates')
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'openwisp_utils.loaders.DependencyLoader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'openwisp_utils.admin_theme.context_processor.menu_groups',
            ],
        },
    }
]

AUTHENTICATION_BACKENDS = [
    'openwisp_users.backends.UsersAuthenticationBackend',
]

if not TESTING and SHELL:
    INSTALLED_APPS.remove('reversion')
    LOGGING = {
        'disable_existing_loggers': False,
        'version': 1,
        'handlers': {
            'console': {
                # logging handler that outputs log messages to terminal
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',  # message level to be written to console
            }
        },
        'loggers': {
            '': {
                # this sets root level logger to log debug and higher level
                # logs to console. All other loggers inherit settings from
                # root level logger.
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'django.db': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }


if not TESTING:
    CELERY_BROKER_URL = 'redis://localhost/6'
else:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'

CELERY_BEAT_SCHEDULE = {
    'password_expiry_email': {
        'task': 'openwisp_users.tasks.password_expiration_email',
        'schedule': crontab(hour=1, minute=0),
    },
}

# during development only
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
LOGIN_REDIRECT_URL = 'admin:index'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'email_confirmation_success'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'email_confirmation_success'

if not PARALLEL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost/0',
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
# parallel testing with redis cache does not work
# so we use the local memory cache in this case
# we still keep redis for the standard non parallel tests
# to avoid having bad surprises in production
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'openwisp-users',
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

if SAMPLE_APP:
    users_index = INSTALLED_APPS.index('openwisp_users')
    INSTALLED_APPS.insert(users_index, 'openwisp2.sample_users')
    INSTALLED_APPS.remove('openwisp_users')
    EXTENDED_APPS = ['openwisp_users']
    AUTH_USER_MODEL = 'sample_users.User'
    OPENWISP_USERS_GROUP_MODEL = 'sample_users.Group'
    OPENWISP_USERS_ORGANIZATION_MODEL = 'sample_users.Organization'
    OPENWISP_USERS_ORGANIZATIONUSER_MODEL = 'sample_users.OrganizationUser'
    OPENWISP_USERS_ORGANIZATIONOWNER_MODEL = 'sample_users.OrganizationOwner'
    OPENWISP_USERS_ORGANIZATIONINVITATION_MODEL = 'sample_users.OrganizationInvitation'

if os.environ.get('NO_SOCIAL_APP', False):
    INSTALLED_APPS.remove('allauth.socialaccount')

# local settings must be imported before test runner otherwise they'll be ignored
try:
    from .local_settings import *
except ImportError:
    pass

# Added for silencing warnings raised by django-all-auth
# on Django 3.2 and above. Remove when new version of
# django-all-auth is released
SILENCED_SYSTEM_CHECKS = ['models.W042']
