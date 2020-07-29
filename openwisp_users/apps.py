import logging

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.utils.translation import ugettext_lazy as _
from openwisp_utils import settings as utils_settings
from swapper import get_model_name, load_model

from . import settings as app_settings

logger = logging.getLogger(__name__)


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
        OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
        Group = load_model('openwisp_users', 'Group')
        User = get_user_model()
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
        for model in [
            User.user_permissions.through,
            User.groups.through,
            Group.permissions.through,
        ]:
            m2m_changed.connect(
                self.update_user_permissions,
                sender=model,
                dispatch_uid='update_user_permissions',
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

    def create_organization_owner(cls, instance, created, **kwargs):
        if not created or not instance.is_admin:
            return
        OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
        OrganizationUser = kwargs.get('sender')
        is_another_org_manager_exist = (
            OrganizationUser.objects.filter(organization=instance.organization)
            .exclude(pk=instance.pk)
            .exists()
        )
        is_org_owner_exist = OrganizationOwner.objects.filter(
            organization_user=instance
        ).exists()
        if not is_another_org_manager_exist and not is_org_owner_exist:
            with transaction.atomic():
                try:
                    owner = OrganizationOwner(
                        organization_user=instance, organization=instance.organization
                    )
                    owner.full_clean()
                    owner.save()
                except ValidationError as e:
                    logger.exception(
                        f'Got exception {type(e)} while saving '
                        f'OrganizationOwner with organization_user {instance} and '
                        f'organization {instance.organization}'
                    )

    def update_user_permissions(cls, instance, action, sender, **kwargs):
        if action == 'post_remove' or action == 'post_add':
            if sender.__name__ == 'Group_permissions':
                for user in instance.user_set.all():
                    cls.update_cached_permissions(user)
            else:
                cls.update_cached_permissions(instance)

    def update_cached_permissions(cls, user):
        cache_key = f'user_{user.pk}_permissions'
        cache.delete(cache_key)
        user.permissions
