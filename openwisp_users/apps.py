import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.signals import post_delete, post_save
from django.utils.translation import gettext_lazy as _
from openwisp_utils import settings as utils_settings
from openwisp_utils.admin_theme.menu import register_menu_group
from swapper import get_model_name, load_model

from . import settings as app_settings

logger = logging.getLogger(__name__)


class OpenwispUsersConfig(AppConfig):
    name = 'openwisp_users'
    app_label = 'openwisp_users'
    verbose_name = _('Users and Organizations')
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        self.register_menu_group()
        self.set_default_settings()
        self.connect_receivers()

    def register_menu_group(self):
        items = {
            1: {
                'label': _('Users'),
                'model': settings.AUTH_USER_MODEL,
                'name': 'changelist',
                'icon': 'user',
            },
            2: {
                'label': _('Organizations'),
                'model': get_model_name(self.app_label, 'Organization'),
                'name': 'changelist',
                'icon': 'ow-org',
            },
            5: {
                'label': _('Groups & Permissions'),
                'model': get_model_name(self.app_label, 'Group'),
                'name': 'changelist',
                'icon': 'ow-permission',
            },
        }
        if app_settings.ORGANIZATION_OWNER_ADMIN:
            items[3] = {
                'label': _('Organization Owners'),
                'model': get_model_name(self.app_label, 'OrganizationOwner'),
                'name': 'changelist',
                'icon': 'ow-org-owner',
            }
        if app_settings.ORGANIZATION_USER_ADMIN:
            items[4] = {
                'label': _('Organization Users'),
                'model': get_model_name(self.app_label, 'OrganizationUser'),
                'name': 'changelist',
                'icon': 'ow-org-user',
            }
        register_menu_group(
            position=40,
            config={
                'label': _('Users & Organizations'),
                'items': items,
                'icon': 'ow-user-and-org',
            },
        )

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

        ACCOUNT_ADAPTER = getattr(settings, 'ACCOUNT_ADAPTER', None)
        if not ACCOUNT_ADAPTER:
            setattr(
                settings,
                'ACCOUNT_ADAPTER',
                'openwisp_users.accounts.adapter.EmailAdapter',
            )

    def connect_receivers(self):
        OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
        OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
        signal_tuples = [(post_save, 'post_save'), (post_delete, 'post_delete')]

        for model in [OrganizationUser, OrganizationOwner]:
            for signal, name in signal_tuples:
                signal.connect(
                    self.update_organizations_dict,
                    sender=model,
                    dispatch_uid='{}_{}_update_organizations_dict'.format(
                        name, model.__name__
                    ),
                )
        post_save.connect(
            self.create_organization_owner,
            sender=OrganizationUser,
            dispatch_uid='make_first_org_user_org_owner',
        )

    def update_organizations_dict(cls, instance, **kwargs):
        if hasattr(instance, 'user'):
            user = instance.user
        else:
            user = instance.organization_user.user
        cache_key = 'user_{}_organizations'.format(user.pk)
        cache.delete(cache_key)
        # forces caching
        user.organizations_dict
        try:
            del user.organizations_managed
        except AttributeError:
            pass
        try:
            del user.organizations_owned
        except AttributeError:
            pass

    def create_organization_owner(cls, instance, created, **kwargs):
        if not created or not instance.is_admin:
            return
        OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
        org_owner_exist = OrganizationOwner.objects.filter(
            organization=instance.organization
        ).exists()
        if not org_owner_exist:
            with transaction.atomic():
                try:
                    owner = OrganizationOwner(
                        organization_user=instance, organization=instance.organization
                    )
                    owner.full_clean()
                    owner.save()
                except (ValidationError, IntegrityError) as e:
                    logger.exception(
                        f'Got exception {type(e)} while saving '
                        f'OrganizationOwner with organization_user {instance} and '
                        f'organization {instance.organization}'
                    )
