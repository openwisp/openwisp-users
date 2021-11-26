import logging
import uuid

import django
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import AbstractUser as BaseUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from swapper import load_model

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def _create_user(self, *args, **kwargs):
        """
        adds automatic email address object creation to django
        management commands "create_user" and "create_superuser"
        """
        user = super()._create_user(*args, **kwargs)
        self._create_email(user)
        return user

    def _create_email(self, user):
        """
        creates verified and primary email address objects
        """
        if user.email:
            set_primary = (
                EmailAddress.objects.filter(user=user, primary=True).count() == 0
            )
            email = EmailAddress.objects.create(
                user=user, email=user.email, verified=True
            )
            if set_primary:
                email.set_as_primary()


class AbstractUser(BaseUser):
    """
    OpenWISP User model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, blank=True, null=True)
    bio = models.TextField(_('bio'), blank=True)
    url = models.URLField(_('URL'), blank=True)
    company = models.CharField(_('company'), max_length=30, blank=True)
    location = models.CharField(_('location'), max_length=256, blank=True)
    phone_number = PhoneNumberField(
        _('phone number'), unique=True, blank=True, null=True
    )
    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    notes = models.TextField(
        _('notes'), help_text=_('notes for internal usage'), blank=True
    )
    language = models.CharField(
        max_length=8,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )

    objects = UserManager()

    class Meta(BaseUser.Meta):
        abstract = True
        index_together = ('id', 'email')

    @staticmethod
    def _get_pk(obj):
        """meant for internal usage only"""
        if isinstance(obj, (uuid.UUID, str)):
            pk = obj
        elif isinstance(obj, BaseOrganization):
            pk = obj.pk
        elif obj is None:
            return None
        else:
            raise ValueError('expected UUID, str or Organization instance')
        return str(pk)

    def is_member(self, organization):
        return self._get_pk(organization) in self.organizations_dict

    def is_manager(self, organization):
        org_dict = self.organizations_dict.get(self._get_pk(organization))
        return org_dict is not None and (org_dict['is_admin'] or org_dict['is_owner'])

    def is_owner(self, organization):
        org_dict = self.organizations_dict.get(self._get_pk(organization))
        return org_dict is not None and org_dict['is_owner']

    @cached_property
    def is_owner_of_any_organization(self):
        for value in self.organizations_dict.values():
            if value['is_owner']:
                return True
        return False

    @property
    def organizations_dict(self):
        """
        Returns a dictionary which represents the organizations which
        the user is member of, or which the user manages or owns.
        """
        cache_key = 'user_{}_organizations'.format(self.pk)
        organizations = cache.get(cache_key)
        if organizations is not None:
            return organizations

        manager = load_model('openwisp_users', 'OrganizationUser').objects
        org_users = manager.filter(
            user=self, organization__is_active=True
        ).select_related('organization', 'organizationowner')

        organizations = {}
        for org_user in org_users:
            org = org_user.organization
            org_id = str(org.pk)
            organizations[org_id] = {
                'is_admin': org_user.is_admin,
                'is_owner': hasattr(org_user, 'organizationowner'),
            }

        cache.set(cache_key, organizations, 86400 * 2)  # Cache for two days
        return organizations

    def __get_orgs(self, attribute):
        org_list = []
        for org_pk, options in self.organizations_dict.items():
            if options[attribute]:
                org_list.append(org_pk)
        return org_list

    @cached_property
    def organizations_managed(self):
        return self.__get_orgs('is_admin')

    @cached_property
    def organizations_owned(self):
        return self.__get_orgs('is_owner')

    def clean(self):
        if self.email == '':
            self.email = None
        if self.phone_number == '':
            self.phone_number = None
        if (
            self.email
            and self._meta.model.objects.filter(email__iexact=self.email)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {'email': _('User with this Email address already exists.')}
            )


# on django 3.1, the max length of first_name has been changed, we need to
# backport this change to the previous versions to avoid migration issues
# TODO: remove this when support to django < 3.1 is dropped
if django.VERSION < (3, 1):
    first_name = AbstractUser._meta.get_field('first_name')
    first_name.max_length = 150


class BaseGroup(object):
    """
    Proxy model used to move ``GroupAdmin``
    under the same app label as the other models
    """

    class Meta:
        proxy = True
        verbose_name = _('group')
        verbose_name_plural = _('groups')


class BaseOrganization(models.Model):
    """
    OpenWISP Organization model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(_('description'), blank=True)
    email = models.EmailField(_('email'), blank=True)
    url = models.URLField(_('URL'), blank=True)

    def __str__(self):
        value = self.name
        if not self.is_active:
            value = '{0} ({1})'.format(value, _('disabled'))
        return value

    class Meta:
        abstract = True


class BaseOrganizationUser(models.Model):
    """
    OpenWISP OrganizationUser model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

    def clean(self):
        if self.user.is_owner(self.organization_id) and not self.is_admin:
            raise ValidationError(
                _(
                    f'{self.user.username} is the owner of the organization: '
                    f'{self.organization}, and cannot be downgraded'
                )
            )


class BaseOrganizationOwner(models.Model):
    """
    OpenWISP OrganizationOwner model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def clean(self):
        if self.organization_user.organization.pk != self.organization.pk:
            raise ValidationError(
                {
                    'organization_user': _(
                        'The selected user is not member of this organization.'
                    )
                }
            )

    class Meta:
        abstract = True
