from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from .throttling import AuthRateThrottle


class ObtainAuthTokenView(ObtainAuthToken):
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    metadata_class = api_settings.DEFAULT_METADATA_CLASS
    versioning_class = api_settings.DEFAULT_VERSIONING_CLASS


obtain_auth_token = ObtainAuthTokenView.as_view()
