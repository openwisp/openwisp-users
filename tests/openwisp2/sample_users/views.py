from openwisp_users.api.views import ChangePasswordView as BaseChangePasswordView
from openwisp_users.api.views import EmailUpdateView as BaseEmailUpdateView
from openwisp_users.api.views import GroupDetailView as BaseGroupDetailView
from openwisp_users.api.views import GroupListCreateView as BaseGroupListCreateView
from openwisp_users.api.views import ObtainAuthTokenView as BaseObtainAuthTokenView
from openwisp_users.api.views import (
    OrganizationDetailView as BaseOrganizationDetailView,
)
from openwisp_users.api.views import (
    OrganizationListCreateView as BaseOrganizationListCreateView,
)
from openwisp_users.api.views import UserDetailView as BaseUserDetailView
from openwisp_users.api.views import UsersListCreateView as BaseUsersListCreateView


class ObtainAuthTokenView(BaseObtainAuthTokenView):
    pass


class OrganizationListCreateView(BaseOrganizationListCreateView):
    pass


class UsersListCreateView(BaseUsersListCreateView):
    pass


class UserDetailView(BaseUserDetailView):
    pass


class OrganizationDetailView(BaseOrganizationDetailView):
    pass


class GroupListCreateView(BaseGroupListCreateView):
    pass


class GroupDetailView(BaseGroupDetailView):
    pass


class ChangePasswordView(BaseChangePasswordView):
    pass


class EmailUpdateView(BaseEmailUpdateView):
    pass


obtain_auth_token = ObtainAuthTokenView.as_view()
organization_list = OrganizationListCreateView.as_view()
organization_detail = OrganizationDetailView.as_view()
user_list = UsersListCreateView.as_view()
user_detail = UserDetailView.as_view()
group_list = GroupListCreateView.as_view()
group_detail = GroupDetailView.as_view()
change_password = ChangePasswordView.as_view()
email_update = EmailUpdateView.as_view()
