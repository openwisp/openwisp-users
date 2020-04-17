from django.core.cache import cache
from django.test import RequestFactory, TestCase
from openwisp_users.api.authentication import BearerAuthentication
from openwisp_users.tests.utils import TestMultitenantAdminMixin
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from . import AuthenticationMixin


class AuthenticationTests(TestMultitenantAdminMixin, AuthenticationMixin, TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.operator = self._create_operator()

    def test_bearer_authentication(self):
        @api_view(['GET'])
        @authentication_classes([BearerAuthentication])
        def my_view(request):
            return Response({})

        request = self.factory.get('/')
        response = my_view(request)
        self.assertEqual(response.status_code, 401)

        token = self._obtain_auth_token()
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer ' + token)
        response = my_view(request)
        self.assertEqual(response.status_code, 200)
