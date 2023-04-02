from django_filters import rest_framework as filters

from .mixins import FilterDjangoByOrgManaged


class BaseOrganizationManagedFilter(FilterDjangoByOrgManaged):
    """
    The Django Filter class that can be used across various OpenWISP
    API views to filter options based on the organization managed by the user
    """

    organization_slug = filters.CharFilter(field_name='organization__slug')

    class Meta:
        fields = ['organization', 'organization_slug']
