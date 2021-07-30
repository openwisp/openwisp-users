from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import pagination, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import (
    GenericAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from swapper import load_model

from openwisp_users.api.authentication import BearerAuthentication
from openwisp_users.api.permissions import DjangoModelPermissions

from .serializers import (
    ChangePasswordSerializer,
    GroupSerializer,
    OrganizationSerializer,
    SuperUserDetailSerializer,
    SuperUserListSerializer,
)
from .swagger import ObtainTokenRequest, ObtainTokenResponse
from .throttling import AuthRateThrottle

Group = load_model('openwisp_users', 'Group')
Organization = load_model('openwisp_users', 'Organization')
User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


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


class BaseOrganizationView(ProtectedAPIMixin):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.order_by('-created')

        return Organization.objects.filter(pk__in=user.organizations_managed).order_by(
            '-created'
        )


class OrganizationListCreateView(BaseOrganizationView, ListCreateAPIView):
    pagination_class = ListViewPagination


class OrganizationDetailView(BaseOrganizationView, RetrieveUpdateDestroyAPIView):
    pass


class BaseUserView(ProtectedAPIMixin):
    serializer_class = SuperUserListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.order_by('-date_joined')

        if not user.is_superuser:
            org_users = OrganizationUser.objects.filter(user=user).select_related(
                'organization'
            )
            qs = User.objects.none()
            for org_user in org_users:
                if org_user.is_admin:
                    qs = qs | org_user.organization.users.all().distinct()
            qs = qs.filter(is_superuser=False)
            return qs.order_by('-date_joined')


class UsersListCreateView(BaseUserView, ListCreateAPIView):
    pagination_class = ListViewPagination


class UserDetailView(BaseUserView, RetrieveUpdateDestroyAPIView):
    serializer_class = SuperUserDetailSerializer


class GroupListCreateView(ProtectedAPIMixin, ListCreateAPIView):
    queryset = Group.objects.prefetch_related('permissions').order_by('name')
    serializer_class = GroupSerializer
    pagination_class = ListViewPagination


class GroupDetailView(ProtectedAPIMixin, RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.order_by('name')
    serializer_class = GroupSerializer


class UpdateAPIView(UpdateModelMixin, GenericAPIView):
    """
    Concrete view for updating a model instance.
    """

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class ChangePasswordView(BaseUserView, UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        user = User.objects.filter(id=self.request.user.id)
        qs = self.get_queryset()
        if (
            user.first().is_staff is True
            and not qs.filter(pk=self.request.user.id).exists()
        ):
            qs = qs | user
        filter_kwargs = {
            'id': self.kwargs['pk'],
        }
        obj = get_object_or_404(qs, **filter_kwargs)
        return obj

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if not user.check_password(request.data.get('old_password')):
            return Response(
                {'old_password': [_('You have entered a wrong password.')]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(request.data.get('new_password'))
        user.save()
        response = {'status': 'success', 'message': _('Password updated successfully')}
        return Response(response)


obtain_auth_token = ObtainAuthTokenView.as_view()
organization_list = OrganizationListCreateView.as_view()
organization_detail = OrganizationDetailView.as_view()
users_list = UsersListCreateView.as_view()
users_detail = UserDetailView.as_view()
group_list = GroupListCreateView.as_view()
group_detail = GroupDetailView.as_view()
change_password = ChangePasswordView.as_view()
