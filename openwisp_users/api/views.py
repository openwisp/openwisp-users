from allauth.account.models import EmailAddress
from allauth.account.utils import user_pk_to_url_str
from dj_rest_auth.views import PasswordChangeView as BasePasswordChangeView
from dj_rest_auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView
from dj_rest_auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.models import Token
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

from openwisp_users.api.permissions import DjangoModelPermissions
from openwisp_users.auth import record_password_based_token
from openwisp_users.backends import UsersAuthenticationBackend
from openwisp_utils.api.pagination import OpenWispPagination

from .mixins import FilterByParent
from .mixins import ProtectedAPIMixin as BaseProtectedAPIMixin
from .serializers import (
    ChangePasswordSerializer,
    EmailAddressSerializer,
    GroupSerializer,
    OrganizationDetailSerializer,
    OrganizationSerializer,
    SuperUserDetailSerializer,
    SuperUserListSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from .swagger import ObtainTokenRequest, ObtainTokenResponse
from .throttling import AuthRateThrottle

Group = load_model("openwisp_users", "Group")
Organization = load_model("openwisp_users", "Organization")
User = get_user_model()
OrganizationUser = load_model("openwisp_users", "OrganizationUser")


class ProtectedAPIMixin(BaseProtectedAPIMixin):
    permission_classes = (
        IsAuthenticated,
        DjangoModelPermissions,
    )


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
        """
        Record the authentication method when issuing a token.

        This endpoint is stateless, so there is no session marker to identify how
        subsequent authenticated requests were established. Persisting
        ``password_based_token`` here ensures token-authenticated requests can
        distinguish password-issued tokens from those obtained through external
        authentication.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _created = Token.objects.get_or_create(user=user)
        record_password_based_token(user, True)
        return Response({"token": token.key})


class PasswordResetView(BasePasswordResetView):
    """
    Requests a password reset e-mail for a user identified by username,
    e-mail address or phone number, mirroring the identifiers accepted at
    local login.
    """

    throttle_classes = [AuthRateThrottle]

    def get_users(self, identifier):
        return UsersAuthenticationBackend().get_users(identifier).filter(is_active=True)

    def get_password_reset_url(self, user, token):
        """
        Returns allauth's HTML password reset URL,
        which is used in the e-mail sent to the user.
        """
        uidb36 = user_pk_to_url_str(user)
        key_path = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": uidb36, "key": token},
        )
        return self.request.build_absolute_uri(key_path)


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    """
    Sets a new password given a valid uid/token pair.

    Unlike PasswordResetView, an invalid uid/token still returns a plain
    400: the pair is already an unguessable secret, so there is nothing
    left to enumerate (see dj-rest-auth's PasswordResetConfirmSerializer,
    reused unchanged below).
    """

    throttle_classes = [AuthRateThrottle]

    def validate_user(self, user):
        """
        No-op extension point: openwisp-radius overrides this to reject a
        reset when the user is not a member of the requesting organization.
        """
        pass

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.validate_user(serializer.user)
        serializer.save()
        return Response({"detail": _("Password has been reset with the new password.")})


class BaseOrganizationView(ProtectedAPIMixin):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.order_by("-created")
        if user.is_anonymous:
            return
        return Organization.objects.filter(pk__in=user.organizations_managed).order_by(
            "-created"
        )


class OrganizationListCreateView(BaseOrganizationView, ListCreateAPIView):
    pagination_class = OpenWispPagination


class OrganizationDetailView(BaseOrganizationView, RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationDetailSerializer


class BaseUserView(ProtectedAPIMixin):
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.order_by("-date_joined")

        if not user.is_superuser and not user.is_anonymous:
            org_users = OrganizationUser.objects.filter(user=user).select_related(
                "organization"
            )
            qs = User.objects.none()
            for org_user in org_users:
                if org_user.is_admin:
                    qs = qs | org_user.organization.users.all().distinct()
            qs = qs.filter(is_superuser=False)
            return qs.order_by("-date_joined")


class UsersListCreateView(BaseUserView, ListCreateAPIView):
    pagination_class = OpenWispPagination

    def get_serializer_class(self):
        user = self.request.user
        if user.is_superuser:
            return SuperUserListSerializer
        return UserListSerializer


class UserDetailView(BaseUserView, RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        user = self.request.user
        if user.is_superuser:
            return SuperUserDetailSerializer
        return UserDetailSerializer


class GroupListCreateView(ProtectedAPIMixin, ListCreateAPIView):
    queryset = Group.objects.prefetch_related(
        "permissions", "permissions__content_type"
    ).order_by("name")
    serializer_class = GroupSerializer
    pagination_class = OpenWispPagination


class GroupDetailView(ProtectedAPIMixin, RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.prefetch_related(
        "permissions", "permissions__content_type"
    ).order_by("name")
    serializer_class = GroupSerializer


class UpdateAPIView(UpdateModelMixin, GenericAPIView):
    """
    Concrete view for updating a model instance.
    """

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class ChangePasswordView(BaseUserView, UpdateAPIView):
    serializer_class = ChangePasswordSerializer

    def get_permissions(self):
        """
        Remove `DangoModelPermissions` permission
        class if loggedin user wants to change
        his own password.
        """
        if self.request.user.id == self.kwargs["pk"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, DjangoModelPermissions]
        return super(self.__class__, self).get_permissions()

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            # To get rid of assertion error raised in
            # the dev server, and for schema generation
            return User.objects.none()

        user = User.objects.filter(id=self.request.user.id)
        qs = self.get_queryset()
        if (
            user.first().is_staff is True
            and not qs.filter(pk=self.request.user.id).exists()
        ):
            qs = qs | user
        filter_kwargs = {
            "id": self.kwargs["pk"],
        }
        obj = get_object_or_404(qs, **filter_kwargs)
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.get_object()
        return context

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"status": "Success", "message": _("Password updated successfully")}
        )


class PasswordChangeView(ProtectedAPIMixin, BasePasswordChangeView):
    """
    Self-service password change endpoint for authenticated users.
    """

    throttle_classes = [AuthRateThrottle]
    # Intentional difference from ``ProtectedAPIMixin``: permission_classes
    # here need to check only that the user is authenticated and nothing
    # else, but authentication_classes are reused.
    permission_classes = (IsAuthenticated,)


class BaseEmailView(ProtectedAPIMixin, FilterByParent, GenericAPIView):
    model = EmailAddress
    serializer_class = EmailAddressSerializer

    def get_queryset(self):
        return EmailAddress.objects.select_related("user").order_by("id")

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.assert_parent_exists()

    def get_parent_queryset(self):
        qs = User.objects.filter(pk=self.kwargs["pk"])
        if self.request.user.is_superuser:
            return qs
        return self.get_organization_queryset(qs)

    def get_organization_queryset(self, qs):
        orgs = self.request.user.organizations_managed
        app_label = User._meta.app_config.label
        filter_kwargs = {
            # exclude superusers
            "is_superuser": False,
            # ensure user is member of the org
            f"{app_label}_organizationuser__organization_id__in": orgs,
        }
        return qs.filter(**filter_kwargs).distinct()

    def get_serializer_context(self):
        if getattr(self, "swagger_fake_view", False):
            # To get rid of assertion error raised in
            # the dev server, and for schema generation
            return None
        context = super().get_serializer_context()
        context["user"] = self.get_parent_queryset().first()
        return context


class EmailListCreateView(BaseEmailView, ListCreateAPIView):
    pagination_class = OpenWispPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            # To get rid of assertion error raised in
            # the dev server, and for schema generation
            return EmailAddress.objects.none()
        return super().get_queryset().filter(user_id=self.kwargs["pk"])


class EmailUpdateView(BaseEmailView, RetrieveUpdateDestroyAPIView):
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(user=self.get_parent_queryset().first())
        filter_kwargs = {
            "id": self.kwargs["email_id"],
        }
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


obtain_auth_token = ObtainAuthTokenView.as_view()
password_reset = PasswordResetView.as_view()
password_reset_confirm = PasswordResetConfirmView.as_view()
organization_list = OrganizationListCreateView.as_view()
organization_detail = OrganizationDetailView.as_view()
user_list = UsersListCreateView.as_view()
user_detail = UserDetailView.as_view()
group_list = GroupListCreateView.as_view()
group_detail = GroupDetailView.as_view()
change_password = ChangePasswordView.as_view()
password_change = PasswordChangeView.as_view()
email_update = EmailUpdateView.as_view()
email_list = EmailListCreateView.as_view()
