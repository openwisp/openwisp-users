from django.contrib.auth.models import Group as AbstractGroup
from django.core.validators import RegexValidator
from django.db import models
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationInvitation,
    AbstractOrganizationOwner,
    AbstractOrganizationUser,
)

from openwisp_users.base.models import (
    AbstractUser,
    BaseGroup,
    BaseOrganization,
    BaseOrganizationOwner,
    BaseOrganizationUser,
)


class DetailsModel(models.Model):
    """
    You do not need to copy this model in your
    application it is only for testing purposes.
    This field serves no purpose, it only serves as an example
    for extending models and used for testing purposes.
    It will be inherited by all the models.
    """

    details = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        abstract = True


class User(DetailsModel, AbstractUser):
    # Remember to set `blank=False` if you don't want your users to
    # skip filling this information.
    social_security_number = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        validators=[RegexValidator(r'^\d\d\d-\d\d-\d\d\d\d$')],
    )

    class Meta(AbstractUser.Meta):
        abstract = False


class Organization(DetailsModel, BaseOrganization, AbstractOrganization):
    pass


class OrganizationUser(DetailsModel, BaseOrganizationUser, AbstractOrganizationUser):
    pass


class OrganizationOwner(DetailsModel, BaseOrganizationOwner, AbstractOrganizationOwner):
    pass


# only needed for django-organizations~=2.x
class OrganizationInvitation(AbstractOrganizationInvitation):
    pass


class Group(DetailsModel, BaseGroup, AbstractGroup):
    pass


#########################################
# You do not need to copy the following in
# your application it is only for module
# testing purposes.
#########################################


class UserInlineModel(DetailsModel, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class OrganizationInlineModel(DetailsModel, models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
