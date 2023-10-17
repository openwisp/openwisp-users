from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse


class StaffUserPasswordExpirationLoginView(BaseLoginView):
    def get_redirect_url(self):
        redirect_to = super().get_redirect_url()
        if redirect_to:
            # The request has redirect URL (next) parameter.
            # The user should be redirected to "account_post_login_redirect" view
            # for the password expiration check first before redirecting them
            # to the desired page.
            redirect_to = '{0}?post_login_redirect={1}'.format(
                reverse('account_post_login_redirect'),
                redirect_to,
            )
        return redirect_to
