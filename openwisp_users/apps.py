from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from openwisp_users import settings as app_settings


class OpenwispUsersConfig(AppConfig):
    name = 'openwisp_users'
    app_label = 'openwisp_users'
    verbose_name = _('Users and Organizations')

    rest_framework_defaults = {
        'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated']
    }

    def ready(self, *args, **kwargs):
        super().ready(*args, **kwargs)
        self.add_default_menu_items()
        self.configure_rest_framework()

    def add_default_menu_items(self):
        menu_setting = 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'
        items = [
            {'model': 'openwisp_users.User'},
            {'model': 'openwisp_users.Organization'},
        ]
        if not hasattr(settings, menu_setting):
            setattr(settings, menu_setting, items)
        else:
            current_menu = getattr(settings, menu_setting)
            current_menu += items

    def configure_rest_framework(self):
        if not app_settings.USERS_AUTH_API:
            return
        user_settings = getattr(settings, 'REST_FRAMEWORK', {})
        self.rest_framework_defaults.update(user_settings)
        setattr(settings, 'REST_FRAMEWORK', self.rest_framework_defaults)
