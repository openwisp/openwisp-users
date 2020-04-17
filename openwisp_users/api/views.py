from rest_framework.authtoken.views import ObtainAuthToken

from .throttling import AuthRateThrottle


class ObtainAuthTokenView(ObtainAuthToken):
    throttle_classes = [AuthRateThrottle]


obtain_auth_token = ObtainAuthTokenView.as_view()
