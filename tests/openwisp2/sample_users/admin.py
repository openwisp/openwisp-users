from openwisp_users import admin
from openwisp_users.utils import (
    usermodel_add_form,
    usermodel_change_form,
    usermodel_list_and_search,
)

# Fields to be added in the UserAdmin
additional_fields = [
    #   [position-of-field-in-form, name-of-field]
    [2, 'social_security_number']
]

# Add field to the User sign up form
usermodel_add_form(admin.UserAdmin, additional_fields)
# Add field to the user profile page
usermodel_change_form(admin.UserAdmin, additional_fields)
# Add field to the admin / operator display_list on changelist view
# and make it searchable.
usermodel_list_and_search(admin.UserAdmin, additional_fields)


#########################################
# You do not need to copy the following in
# your application it is only for module
# testing purposes.
#########################################

from django.contrib.admin import StackedInline  # noqa

from .models import OrganizationInlineModel, UserInlineModel  # noqa


class UserInlineAdmin(StackedInline):
    model = UserInlineModel


class OrganizationInlineAdmin(StackedInline):
    model = OrganizationInlineModel


admin.UserAdmin.inlines += (UserInlineAdmin,)
admin.OrganizationAdmin.inlines += (OrganizationInlineAdmin,)
