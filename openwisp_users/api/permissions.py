from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')


class BaseOrganizationPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        organization = self.get_object_organization(view, obj)
        return self.validate_membership(request.user, organization)

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def get_object_organization(self, view, obj):
        organization_field = getattr(view, 'organization_field', 'organization')
        fields = organization_field.split('__')
        accessed_object = obj
        for field in fields:
            accessed_object = getattr(accessed_object, field, None)
            if not accessed_object:
                raise AttributeError(
                    _(
                        'Organization not found, `organization_field` '
                        'not implemented correctly.'
                    )
                )
        return accessed_object

    def validate_membership(self, user, org):
        raise NotImplementedError(
            _(
                'View\'s permission_classes not implemented correctly.'
                'Please use one of the child classes: IsOrganizationMember, '
                'IsOrganizationManager or IsOrganizationOwner.'
            )
        )


class IsOrganizationMember(BaseOrganizationPermission):
    message = _(
        'User is not a member of the organization to which the '
        'requested resource belongs.'
    )

    def validate_membership(self, user, org):
        return org and (user.is_superuser or user.is_member(org))


class IsOrganizationManager(BaseOrganizationPermission):
    message = _(
        'User is not a manager of the organization to which the '
        'requested resource belongs.'
    )

    def validate_membership(self, user, org):
        return org and (user.is_superuser or user.is_manager(org))


class IsOrganizationOwner(BaseOrganizationPermission):
    message = _(
        'User is not a owner of the organization to which the '
        'requested resource belongs.'
    )

    def validate_membership(self, user, org):
        return org and (user.is_superuser or user.is_owner(org))
