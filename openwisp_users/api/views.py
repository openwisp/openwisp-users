from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from .swagger import ObtainTokenRequest, ObtainTokenResponse
from .throttling import AuthRateThrottle


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


obtain_auth_token = ObtainAuthTokenView.as_view()
