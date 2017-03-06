from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class OpenwispUsersConfig(AppConfig):
    name = 'openwisp_users'
    app_label = 'openwisp_users'
    verbose_name = _('Users and Organizations')
