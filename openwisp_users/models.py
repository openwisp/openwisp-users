import swapper
from django.contrib.auth.models import Group as AbstractGroup
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationInvitation,
    AbstractOrganizationOwner,
    AbstractOrganizationUser,
)

from .base.models import (
    AbstractUser,
    BaseGroup,
    BaseOrganization,
    BaseOrganizationOwner,
    BaseOrganizationUser,
)


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        abstract = False


class Organization(BaseOrganization, AbstractOrganization):
    class Meta(AbstractOrganization.Meta):
        swapper.swappable_setting('openwisp_users', 'Organization')


class OrganizationUser(BaseOrganizationUser, AbstractOrganizationUser):
    class Meta(AbstractOrganizationUser.Meta):
        swapper.swappable_setting('openwisp_users', 'OrganizationUser')


class OrganizationOwner(BaseOrganizationOwner, AbstractOrganizationOwner):
    class Meta(AbstractOrganizationOwner.Meta):
        swapper.swappable_setting('openwisp_users', 'OrganizationOwner')


# only needed for django-organizations~=2.x
class OrganizationInvitation(AbstractOrganizationInvitation):
    class Meta(AbstractOrganizationInvitation.Meta):
        swapper.swappable_setting('openwisp_users', 'OrganizationInvitation')


class Group(BaseGroup, AbstractGroup):
    class Meta(BaseGroup.Meta):
        swapper.swappable_setting('openwisp_users', 'Group')
