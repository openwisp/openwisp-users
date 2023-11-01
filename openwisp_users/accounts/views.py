from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView


class PostLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.has_password_expired():
            messages.warning(
                self.request,
                _('Your password has expired, please update your password.'),
            )
            if user.is_staff:
                return reverse('admin:auth_user_password_change', args=[user.id])
            return reverse('account_change_password')
        return self.request.GET.get('post_login_redirect', reverse('admin:index'))


post_login_redirect = PostLoginRedirectView.as_view()
