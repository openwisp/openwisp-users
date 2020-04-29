from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class OpenwispUsersConfig(AppConfig):
    name = 'openwisp_users'
    app_label = 'openwisp_users'
    verbose_name = _('Users and Organizations')

    def ready(self, *args, **kwargs):
        super().ready(*args, **kwargs)
        self.add_default_menu_items()

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
