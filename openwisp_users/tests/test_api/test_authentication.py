from django.core.cache import cache
from django.test import RequestFactory
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openwisp_users.api.authentication import BearerAuthentication

from . import APITestCase


class AuthenticationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.operator = self._create_operator()

    def test_bearer_authentication(self):
        @api_view(['GET'])
        @permission_classes([IsAuthenticated])
        @authentication_classes([BearerAuthentication])
        def my_view(request):
            return Response({})

        request = self.factory.get('/')
        response = my_view(request)
        self.assertEqual(response.status_code, 401)

        token = self._obtain_auth_token()
        request = self.factory.get('/', HTTP_AUTHORIZATION=f'Bearer {token}')
        response = my_view(request)
        self.assertEqual(response.status_code, 200)
