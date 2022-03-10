import swapper
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

Organization = swapper.load_model('openwisp_users', 'Organization')


class OrgLookup:
    @property
    def org_field(self):
        return getattr(self, 'organization_field', 'organization')

    @property
    def organization_lookup(self):
        return f'{self.org_field}__in'


class SharedObjectsLookup:
    @property
    def queryset_organization_conditions(self):
        conditions = super().queryset_organization_conditions
        organizations = getattr(self.request.user, self._user_attr)
        # If user has access to any organization, then include shared
        # objects in the queryset.
        if len(organizations):
            conditions |= Q(**{f'{self.org_field}__isnull': True})
        return conditions


class FilterByOrganization(OrgLookup):
    """
    Filter queryset based on the access to the organization
    of the associated model. Use on of the sub-classes
    """

    permission_classes = (IsAuthenticated,)

    @property
    def _user_attr(self):
        raise NotImplementedError()

    @property
    def queryset_organization_conditions(self):
        return Q(
            **{self.organization_lookup: getattr(self.request.user, self._user_attr)}
        )

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return self.get_organization_queryset(qs)

    def get_organization_queryset(self, qs):
        if self.request.user.is_anonymous:
            return
        return qs.filter(self.queryset_organization_conditions)


class FilterByOrganizationMembership(FilterByOrganization):
    """
    Filter queryset by organizations the user is a member of
    """

    _user_attr = 'organizations_dict'


class FilterByOrganizationManaged(SharedObjectsLookup, FilterByOrganization):
    """
    Filter queryset by organizations managed by user
    """

    _user_attr = 'organizations_managed'


class FilterByOrganizationOwned(SharedObjectsLookup, FilterByOrganization):
    """
    Filter queryset by organizations owned by user
    """

    _user_attr = 'organizations_owned'


class FilterByParent(OrgLookup):
    """
    Filter queryset based on one of the parent objects
    """

    permission_classes = (IsAuthenticated,)

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
            raise NotFound()

    def get_organization_queryset(self, qs):
        lookup = {self.organization_lookup: getattr(self.request.user, self._user_attr)}
        return qs.filter(**lookup)

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


class FilterSerializerByOrganization(OrgLookup):
    """
    Filter the options in browsable API for serializers
    """

    include_shared = False

    @property
    def _user_attr(self):
        raise NotImplementedError()

    def filter_fields(self):
        user = self.context['request'].user
        # superuser can see everything
        if user.is_superuser or user.is_anonymous:
            return
        # non superusers can see only items of organizations they're related to
        organization_filter = getattr(user, self._user_attr)
        for field in self.fields:
            if field == 'organization' and not self.fields[field].read_only:
                # queryset attribute will not be present if set to read_only
                self.fields[field].allow_null = False
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    pk__in=organization_filter
                )
                continue
            conditions = Q(**{self.organization_lookup: organization_filter})
            if self.include_shared:
                conditions |= Q(organization__isnull=True)
            try:
                self.fields[field].queryset = self.fields[field].queryset.filter(
                    conditions
                )
            except AttributeError:
                pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only filter related fields if the serializer
        # is being initiated during an HTTP request
        if 'request' in self.context:
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
