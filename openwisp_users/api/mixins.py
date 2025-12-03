import swapper
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey, ManyToManyField, Q
from django_filters import rest_framework as filters
from django_filters.filters import QuerySetRequestMixin as BaseQuerySetRequestMixin
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from .authentication import BearerAuthentication
from .permissions import DjangoModelPermissions, IsOrganizationManager

Organization = swapper.load_model("openwisp_users", "Organization")


class OrgLookup:
    @property
    def org_field(self):
        return getattr(self, "organization_field", "organization")

    @property
    def organization_lookup(self):
        return f"{self.org_field}__in"


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
    Filter serializer related-field querysets based on the organizations the
    current user is allowed to access.

    """

    include_shared = False

    @property
    def _user_attr(self):
        raise NotImplementedError()

    def _get_org_related_fields(self, model):
        org_fields = []
        for f in model._meta.get_fields():
            if getattr(f, "is_relation", False) and getattr(f, "related_model", None):
                if f.related_model is Organization:
                    org_fields.append(f.name)
        return org_fields

    def filter_fields(self):
        request = self.context.get("request")
        if not request:
            return

        user = request.user

        # Superusers or anonymous -> no filtering
        if user.is_superuser or user.is_anonymous:
            return

        allowed_orgs = getattr(user, self._user_attr)

        # Detect if user has any organizations (used for include_shared visibility)
        try:
            has_allowed_orgs = bool(allowed_orgs.exists())
        except Exception:
            try:
                has_allowed_orgs = bool(len(allowed_orgs))
            except Exception:
                has_allowed_orgs = bool(allowed_orgs)

        for field_name, field in self.fields.items():
            queryset = getattr(field, "queryset", None)
            if queryset is None:
                continue

            model = getattr(queryset, "model", None)
            if model is None:
                continue

            # CASE A: Field points directly to the Organization model
            if model is Organization:
                try:
                    qs = queryset.filter(pk__in=allowed_orgs)
                    if self.include_shared and has_allowed_orgs:
                        qs = qs | queryset.filter(pk__isnull=True)
                    field.queryset = qs.distinct()
                except Exception:
                    pass

                # Enforce: non-superusers cannot CREATE shared objects
                if field_name == "organization" and not user.is_superuser:
                    try:
                        field.allow_null = False
                        field.required = True
                    except Exception:
                        pass
                continue

            # CASE B: Related model — look for org-related fields
            org_fields = self._get_org_related_fields(model)
            if not org_fields:
                continue

            # Build: org_field__in = allowed_orgs
            conditions = Q()
            for org_field in org_fields:
                conditions |= Q(**{f"{org_field}__in": allowed_orgs})

            # Visibility: include shared objects (organization=None)
            if self.include_shared and has_allowed_orgs:
                null_conditions = Q()
                for org_field in org_fields:
                    null_conditions |= Q(**{f"{org_field}__isnull": True})
                conditions |= null_conditions
            else:
                # Normal users must NOT see shared objects if include_shared=False
                for org_field in org_fields:
                    queryset = queryset.exclude(**{f"{org_field}__isnull": True})

            # Remove nulls entirely if field disallows null
            if not getattr(field, "allow_null", False):
                for org_field in org_fields:
                    queryset = queryset.exclude(**{f"{org_field}__isnull": True})

            try:
                field.queryset = queryset.filter(conditions).distinct()
            except Exception:
                pass

            # If this field is the organization FK on the serializer,
            # enforce NO shared creation for non-superusers
            if field_name == "organization" and not user.is_superuser:
                try:
                    field.allow_null = False
                    field.required = True
                except Exception:
                    pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "request" in self.context:
            self.filter_fields()


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
    )
