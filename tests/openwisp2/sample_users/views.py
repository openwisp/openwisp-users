from openwisp_users.api.views import ObtainAuthTokenView as BaseObtainAuthTokenView


class ObtainAuthTokenView(BaseObtainAuthTokenView):
    pass


obtain_auth_token = ObtainAuthTokenView.as_view()
