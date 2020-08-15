import swapper
from rest_framework.response import Response
from rest_framework.views import APIView

from openwisp_users.api.authentication import BearerAuthentication
from openwisp_users.api.permissions import (
    BaseOrganizationPermission,
    IsOrganizationManager,
    IsOrganizationMember,
    IsOrganizationOwner,
)

from .models import Config, Template

Organization = swapper.load_model('openwisp_users', 'Organization')


class BaseGetApiView(APIView):
    queryset = Template.objects.all()

    def get(self, request, *args, **kwargs):
        testorg, _ = Organization.objects.get_or_create(name='test org')
        template, _ = Template.objects.get_or_create(
            name='sample', organization=testorg
        )
        self.check_object_permissions(request, template)
        return Response({})


class ApiMemberView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)


class ApiManagerView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationManager,)


class ApiOwnerView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationOwner,)


class BaseOrganizationPermissionView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (BaseOrganizationPermission,)


class OrganizationFieldView(APIView):
    queryset = Config.objects.all()
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    organization_field = 'template__organization'

    def get(self, request, *args, **kwargs):
        testorg, _ = Organization.objects.get_or_create(name='test org')
        temp1, _ = Template.objects.get_or_create(name='temp', organization=testorg)
        config, _ = Config.objects.get_or_create(template=temp1, organization=testorg)
        self.check_object_permissions(request, config)
        return Response({})


class ErrorOrganizationFieldView(BaseGetApiView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsOrganizationMember,)
    organization_field = 'error__organization'


api_member_view = ApiMemberView.as_view()
api_manager_view = ApiManagerView.as_view()
api_owner_view = ApiOwnerView.as_view()
base_org_view = BaseOrganizationPermissionView.as_view()
org_field_view = OrganizationFieldView.as_view()
error_field_view = ErrorOrganizationFieldView.as_view()
