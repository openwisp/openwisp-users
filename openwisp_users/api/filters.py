import swapper
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound

Organization = swapper.load_model('openwisp_users', 'Organization')


class FilterByOrganization:
    """
    Filter queryset based on the access to the organization
    of the associated model. Use on of the sub-classes
    """

    @property
    def _user_attr(self):
        raise NotImplementedError()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return self.get_organization_queryset(qs)

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=getattr(self.request.user, self._user_attr))


class FilterByOrganizationMembership(FilterByOrganization):
    """
    Filter queryset by organizations the user is a member of
    """

    _user_attr = 'organizations_dict'


class FilterByOrganizationManaged(FilterByOrganization):
    """
    Filter queryset by organizations managed by user
    """

    _user_attr = 'organizations_managed'


class FilterByOrganizationOwned(FilterByOrganization):
    """
    Filter queryset by organizations owned by user
    """

    _user_attr = 'organizations_owned'


class FilterByParent:
    """
    Filter queryset based on one of the parent objects
    """

    @property
    def _user_attr(self):
        raise NotImplementedError()

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

    def get_organization_queryset(self, qs):
        return qs.filter(organization__in=getattr(self.request.user, self._user_attr))

    def get_parent_queryset(self):
        raise NotImplementedError()


class FilterByParentMembership(FilterByParent):
    """
    Filter queryset based on parent organization membership
    """

    _user_attr = 'organizations_dict'


class FilterByParentManaged(FilterByParent):
    """
    Filter queryset based on parent organizations managed by user
    """

    _user_attr = 'organizations_managed'


class FilterByParentOwned(FilterByParent):
    """
    Filter queryset based on parent organizations owned by user
    """

    _user_attr = 'organizations_owned'


class FilterSerializerByOrganization:
    """
    Filter the options in browsable API for serializers
    """

    @property
    def _user_attr(self):
        raise NotImplementedError()

    def filter_fields(self):
        user = self.context['request'].user
        if user.is_superuser:
            return
        organization_filter = getattr(user, self._user_attr)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_fields()


class FilterSerializerByOrgMembership(FilterSerializerByOrganization):
    """
    Filter serializer by organizations the user is member of
    """

    _user_attr = 'organizations_dict'


class FilterSerializerByOrgManaged(FilterSerializerByOrganization):
    """
    Filter serializer by organizations managed by user
    """

    _user_attr = 'organizations_managed'


class FilterSerializerByOrgOwned(FilterSerializerByOrganization):
    """
    Filter serializer by organizations owned by user
    """

    _user_attr = 'organizations_owned'
