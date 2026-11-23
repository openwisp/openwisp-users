import swapper
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import ForeignKey, ManyToManyField, Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from django_filters.filters import QuerySetRequestMixin as BaseQuerySetRequestMixin
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from .authentication import BearerAuthentication
from .permissions import (
    DisabledOrgReadOnly,
    DjangoModelPermissions,
    IsOrganizationManager,
)

Organization = swapper.load_model("openwisp_users", "Organization")

DISABLED_ORGANIZATION_ERROR_MESSAGE = _(
    'Organization with pk "{pk_value}" does not exist or is disabled.'
)


class OrgLookup:
    select_related_organization = True

    @property
    def org_field(self):
        return getattr(self, "organization_field", "organization")

    @property
    def organization_lookup(self):
        return f"{self.org_field}__in"

    def _organization_relation_is_valid(self, model):
        """Check the path can be joined safely and ends at the Organization model.

        Invalid paths must reach the permission check instead of causing a
        ``select_related`` error before it can deny the write.
        """
        for part in self.org_field.split("__"):
            try:
                field = model._meta.get_field(part)
            except FieldDoesNotExist:
                return False
            if not (field.concrete and (field.many_to_one or field.one_to_one)):
                return False
            model = field.related_model
        return model == Organization


class SharedObjectsLookup:
    @property
    def queryset_organization_conditions(self):
        conditions = super().queryset_organization_conditions
        organizations = getattr(self.request.user, self._user_attr)
        # If user has access to any organization, then include shared
        # objects in the queryset.
        if len(organizations):
            conditions |= Q(**{f"{self.org_field}__isnull": True})
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
        if getattr(
            self, "select_related_organization", True
        ) and self._organization_relation_is_valid(qs.model):
            qs = qs.select_related(self.org_field)
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

    _user_attr = "organizations_dict"


class FilterByOrganizationManaged(SharedObjectsLookup, FilterByOrganization):
    """
    Filter queryset by organizations managed by user
    """

    _user_attr = "organizations_managed"


class FilterByOrganizationOwned(SharedObjectsLookup, FilterByOrganization):
    """
    Filter queryset by organizations owned by user
    """

    _user_attr = "organizations_owned"


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

    _user_attr = "organizations_dict"


class FilterByParentManaged(FilterByParent):
    """
    Filter queryset based on parent organizations managed by user
    """

    _user_attr = "organizations_managed"


class FilterByParentOwned(FilterByParent):
    """
    Filter queryset based on parent organizations owned by user
    """

    _user_attr = "organizations_owned"


class FilterSerializerByOrganization(OrgLookup):
    """
    Filter the options in browsable API for serializers
    """

    include_shared = False

    @property
    def _user_attr(self):
        raise NotImplementedError()

    def filter_fields(self):
        """
        Limit submitted relationships and rendered choices in the browsable API.

        Users can select active organizations within their permitted scope and
        related objects belonging to those organizations. Shared objects are
        included according to the user's role and ``include_shared``.
        """
        user = self.context["request"].user
        organization_filter = None
        if not user.is_superuser and not user.is_anonymous:
            organization_filter = getattr(user, self._user_attr)
        for name, field in self.fields.items():
            if name == "organization" and not field.read_only:
                self._filter_organization_field(field, organization_filter)
            else:
                self._filter_related_field(field, organization_filter)

    def _filter_organization_field(self, field, organization_filter):
        """Limit organization choices without breaking opted-out updates.

        Such updates may keep their current disabled organization, but cannot
        select another disabled organization or create an object in one.
        """
        # Keep disabled organizations out of writable relation fields.
        queryset = field.queryset.filter(is_active=True)
        field.error_messages["does_not_exist"] = DISABLED_ORGANIZATION_ERROR_MESSAGE
        view = self.context.get("view")
        organization = getattr(self.instance, "organization", None)
        # An opted-out view must accept the existing disabled organization
        # when updating the object, without accepting other disabled choices.
        keep_current = (
            getattr(view, "allow_disabled_organization_writes", False)
            and organization is not None
            and not organization.is_active
        )
        if keep_current:
            queryset |= field.queryset.filter(pk=organization.pk)
        if organization_filter is not None:
            field.allow_null = False
            allowed_organizations = Q(pk__in=organization_filter)
            if keep_current:
                allowed_organizations |= Q(pk=organization.pk)
            # Keep the existing disabled organization available only for an
            # opted-out update, without allowing other unmanaged organizations.
            queryset = queryset.filter(allowed_organizations)
        field.queryset = queryset

    def _filter_related_field(self, field, organization_filter):
        # DRF stores a many-valued relation queryset on its child field.
        field = getattr(field, "child_relation", field)
        queryset = getattr(field, "queryset", None)
        # Read-only and non-relational fields do not expose a queryset.
        if queryset is None:
            return
        conditions = Q(**{f"{self.org_field}__is_active": True})
        if organization_filter is None:
            # Superusers and anonymous users have no organization scope here.
            conditions |= Q(**{f"{self.org_field}__isnull": True})
        else:
            conditions &= Q(**{self.organization_lookup: organization_filter})
            if self.include_shared:
                # Some serializers also allow objects shared systemwide.
                conditions |= Q(**{f"{self.org_field}__isnull": True})
        field.queryset = queryset.filter(conditions)

    def _filter_fields_once(self):
        """Wait for request context and avoid adding the same filters repeatedly.

        A nested list reuses its child serializer for every item, so filtering
        on every validation would make its queries grow with the list.
        """
        request = self.context.get("request")
        if request is None or getattr(self, "_filtered_request", None) is request:
            return
        self.filter_fields()
        self._filtered_request = request

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_fields_once()

    def bind(self, field_name, parent):
        """Apply request-based restrictions when this serializer is nested.

        A nested serializer can be initialized before its parent supplies the
        request context, so its relation fields may first be filtered on bind.
        """
        super().bind(field_name, parent)
        self._filter_fields_once()

    def to_internal_value(self, data):
        # A many=True child may bind before the root has request context, so
        # restrict its fields now, before DRF validates submitted relations.
        self._filter_fields_once()
        return super().to_internal_value(data)


class FilterSerializerByOrgMembership(FilterSerializerByOrganization):
    """
    Filter serializer by organizations the user is member of
    """

    _user_attr = "organizations_dict"


class FilterSerializerByOrgManaged(FilterSerializerByOrganization):
    """
    Filter serializer by organizations managed by user
    """

    _user_attr = "organizations_managed"


class FilterSerializerByOrgOwned(FilterSerializerByOrganization):
    """
    Filter serializer by organizations owned by user
    """

    _user_attr = "organizations_owned"


class QuerySetRequestMixin(BaseQuerySetRequestMixin):
    def get_queryset(self, request):
        user = request.user
        queryset = super().get_queryset(request)
        # superuser can see everything
        if user.is_superuser or user.is_anonymous:
            return queryset
        # non superusers can see only items
        # of organizations they're related to
        organization_filter = getattr(user, self._user_attr)
        # if field_name organization then just organization_filter
        if self._filter_field == "organization":
            return queryset.filter(pk__in=organization_filter)
        # for field_name other than organization
        conditions = Q(**{"organization__in": organization_filter})
        return queryset.filter(conditions)

    def __init__(self, *args, **kwargs):
        self._user_attr = kwargs.pop("user_attr")
        self._filter_field = kwargs.pop("filter_field")
        super().__init__(*args, **kwargs)


class DjangoOrganizationFilter(filters.ModelChoiceFilter, QuerySetRequestMixin):
    pass


class DjangoOrganizationM2MFilter(
    filters.ModelMultipleChoiceFilter, QuerySetRequestMixin
):
    pass


class FilterDjangoOrganization(filters.FilterSet):
    """
    A custom filter set class that applies DjangoOrganizationFilter
    to all ModelChoiceFilter & ModelMultipleChoiceFilterfilters.
    """

    @classmethod
    def filter_for_field(cls, field, name, lookup_expr="exact"):
        if isinstance(field, ForeignKey) or isinstance(field, ManyToManyField):
            if field.name == "user":
                return super().filter_for_field(field, name, lookup_expr)
            opts = dict(
                queryset=field.remote_field.model.objects.all(),
                label=field.verbose_name.capitalize(),
                field_name=name,
                user_attr=cls._user_attr,
                filter_field=field.name,
            )
            if isinstance(field, ForeignKey):
                return DjangoOrganizationFilter(**opts)
            if isinstance(field, ManyToManyField):
                return DjangoOrganizationM2MFilter(**opts)
        return super().filter_for_field(field, name, lookup_expr)


class FilterDjangoByOrgMembership(FilterDjangoOrganization):
    """
    Filter django-filters by organizations the user is member of
    """

    _user_attr = "organizations_dict"


class FilterDjangoByOrgManaged(FilterDjangoOrganization):
    """
    Filter django-filters by organizations managed by user
    """

    _user_attr = "organizations_managed"


class FilterDjangoByOrgOwned(FilterDjangoOrganization):
    """
    Filter django-filters by organizations owned by user
    """

    _user_attr = "organizations_owned"


class ProtectedAPIMixin(object):
    """
    Contains authentication and permission classes for API views
    """

    authentication_classes = (
        BearerAuthentication,
        SessionAuthentication,
    )
    permission_classes = (
        IsOrganizationManager,
        DjangoModelPermissions,
        DisabledOrgReadOnly,
    )
