from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import pagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.settings import api_settings
from swapper import load_model

from openwisp_users.api.authentication import BearerAuthentication

from .serializers import OrganizationSerializer, UserSerializer
from .swagger import ObtainTokenRequest, ObtainTokenResponse
from .throttling import AuthRateThrottle

Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()


class ListViewPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ObtainAuthTokenView(ObtainAuthToken):
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    metadata_class = api_settings.DEFAULT_METADATA_CLASS
    versioning_class = api_settings.DEFAULT_VERSIONING_CLASS

    @swagger_auto_schema(
        request_body=ObtainTokenRequest, responses={200: ObtainTokenResponse}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProtectedAPIMixin(object):
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]


class OrganizationListCreateView(ProtectedAPIMixin, ListCreateAPIView):
    queryset = Organization.objects.order_by('-created')
    serializer_class = OrganizationSerializer
    pagination_class = ListViewPagination


class OrganizationDetailView(ProtectedAPIMixin, RetrieveUpdateDestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class UsersListCreateView(ProtectedAPIMixin, ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


obtain_auth_token = ObtainAuthTokenView.as_view()
organization_list = OrganizationListCreateView.as_view()
organization_detail = OrganizationDetailView.as_view()
users_list = UsersListCreateView.as_view()
