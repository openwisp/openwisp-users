from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.utils.translation import ugettext_lazy as _
from openwisp_utils import settings as utils_settings
from swapper import get_model_name, load_model

# from django.dispatch import receiver
from . import settings as app_settings


class OpenwispUsersConfig(AppConfig):
    name = 'openwisp_users'
    app_label = 'openwisp_users'
    verbose_name = _('Users and Organizations')

    def ready(self):
        self.add_default_menu_items()
        self.set_default_settings()
        self.connect_receivers()

    def add_default_menu_items(self):
        menu_setting = 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'
        items = [
            {'model': settings.AUTH_USER_MODEL},
            {'model': get_model_name('openwisp_users', 'Organization')},
        ]
        if not hasattr(settings, menu_setting):
            setattr(settings, menu_setting, items)
        else:
            current_menu = getattr(settings, menu_setting)
            current_menu += items

    def set_default_settings(self):
        LOGIN_URL = getattr(settings, 'LOGIN_URL', None)
        if not LOGIN_URL:
            setattr(settings, 'LOGIN_URL', 'account_login')

        LOGOUT_URL = getattr(settings, 'LOGOUT_URL', None)
        if not LOGOUT_URL:
            setattr(settings, 'LOGOUT_URL', 'account_logout')

        if app_settings.USERS_AUTH_API and utils_settings.API_DOCS:
            SWAGGER_SETTINGS = getattr(settings, 'SWAGGER_SETTINGS', {})
            SWAGGER_SETTINGS['SECURITY_DEFINITIONS'] = {
                'Bearer': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}
            }
            setattr(settings, 'SWAGGER_SETTINGS', SWAGGER_SETTINGS)

    def connect_receivers(self):
        OrganizationUser = load_model('openwisp_users', 'OrganizationUser')

        post_save.connect(
            self.update_organizations_dict,
            sender=OrganizationUser,
            dispatch_uid='post_save_update_organizations_dict',
        )
        post_delete.connect(
            self.update_organizations_dict,
            sender=OrganizationUser,
            dispatch_uid='post_delete_update_organizations_dict',
        )

    def update_organizations_dict(cls, instance, **kwargs):
        cache_key = 'user_{}_organizations'.format(instance.user.pk)
        cache.delete(cache_key)
        # forces caching
        instance.user.organizations_dict
