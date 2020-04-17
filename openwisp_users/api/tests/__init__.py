from django.urls import reverse


class AuthenticationMixin:
    def _obtain_auth_token(self, username='operator', password='tester'):
        params = {'username': username, 'password': password}
        url = reverse('api-token-auth')
        r = self.client.post(url, params)
        return r.data["token"]
