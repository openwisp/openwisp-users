from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.permissions import (
    DjangoModelPermissions as BaseDjangoModelPermissions,
)
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


class DjangoModelPermissions(BaseDjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        user = request.user
        if not user or (not user.is_authenticated and self.authenticated_users_only):
            return False

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)
        change_perm = self.get_required_permissions('PUT', queryset.model)

        if request.method == 'GET':
            return user.has_perms(perms) or user.has_perms(change_perm)

        return user.has_perms(perms)
