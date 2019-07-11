from ..models import Organization
from .generics import (BaseOrganizationListCreateAPIView,
                       BaseOrganizationUpdateDeleteAPIView)


class OrganizationListCreateAPIView(BaseOrganizationListCreateAPIView):
    queryset = Organization.objects.all()
    org_model = Organization


class OrganizationRetrieveUpdateDeleteAPIView(BaseOrganizationUpdateDeleteAPIView):
    queryset = Organization.objects.all()


list_orgs = OrganizationListCreateAPIView.as_view()
org_detail = OrganizationRetrieveUpdateDeleteAPIView.as_view()
