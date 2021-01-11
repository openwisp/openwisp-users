import swapper
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound, PermissionDenied

Organization = swapper.load_model('openwisp_users', 'Organization')


class FilterByOrganization:
    """
    Filter queryset based on the access to the organization
    of the associated model. Use on of the sub-classes
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return self.get_organization_queryset(qs)

    def get_organization_queryset(self):
        raise NotImplementedError()


class FilterByOrganizationMembership(FilterByOrganization):
    """
    Filter queryset by organizations the user is a member of
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_dict)


class FilterByOrganizationManaged(FilterByOrganization):
    """
    Filter queryset by organizations managed by user
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_managed)


class FilterByOrganizationOwned(FilterByOrganization):
    """
    Filter queryset by organizations owned by user
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_owned)


class FilterByParent:
    """
    Filter queryset based on one of the parent objects
    """

    def get_queryset(self):
        qs = super().get_queryset()
        self.assert_parent_exists()
        return qs

    def assert_parent_exists(self):
        parent_queryset = self.get_parent_queryset()
        if not self.request.user.is_superuser:
            parent_queryset = self.get_organization_queryset(parent_queryset)
        try:
            assert parent_queryset.exists()
        except (AssertionError, ValidationError):
            raise NotFound(detail='No relevant data found.')

    def get_parent_queryset(self):
        raise NotImplementedError()

    def get_organization_queryset(self):
        raise NotImplementedError()


class FilterByParentMembership(FilterByParent):
    """
    Filter queryset based on parent organization membership
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_dict)


class FilterByParentManaged(FilterByParent):
    """
    Filter queryset based on parent organizations managed by user
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_managed)


class FilterByParentOwned(FilterByParent):
    """
    Filter queryset based on parent organizations owned by user
    """

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=self.request.user.organizations_owned)


class FilterSerializerByOrganization:
    """
    Filter the options in browsable API for serializers
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context['request'].user.is_superuser:
            return
        self.filter_fields()

    def filter_fields(self):
        raise NotImplementedError()


class FilterSerializerByOrgMembership(FilterSerializerByOrganization):
    """
    Filter serializer by organizations the user is member of
    """

    def filter_fields(self):
        user = self.context['request'].user
        organization_filter = user.organizations_dict
        for field in self.fields:
            if field == 'organization':
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    pk__in=organization_filter
                )
                continue
            try:
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    organization__in=organization_filter
                )
            except AttributeError:
                pass


class FilterSerializerByOrgManaged(FilterSerializerByOrganization):
    """
    Filter serializer by organizations managed by user
    """

    def filter_fields(self):
        user = self.context['request'].user
        organization_filter = user.organizations_managed
        for field in self.fields:
            if field == 'organization':
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    pk__in=organization_filter
                )
                continue
            try:
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    organization__in=organization_filter
                )
            except AttributeError:
                pass


class FilterSerializerByOrgOwned(FilterSerializerByOrganization):
    """
    Filter serializer by organizations owned by user
    """

    def filter_fields(self):
        user = self.context['request'].user
        organization_filter = user.organizations_owned
        for field in self.fields:
            if field == 'organization':
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    pk__in=organization_filter
                )
                continue
            try:
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    organization__in=organization_filter
                )
            except AttributeError:
                pass
