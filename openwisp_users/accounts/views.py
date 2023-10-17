from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from .. import settings as app_settings


class PostLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if (
            app_settings.STAFF_USER_PASSWORD_EXPIRATION
            and user.is_staff
            and timezone.now().date()
            > user.password_updated
            + timezone.timedelta(days=app_settings.STAFF_USER_PASSWORD_EXPIRATION)
        ):
            messages.warning(
                self.request,
                _('Your password has expired, please update your password.'),
            )
            return reverse('admin:auth_user_password_change', args=[user.id])
        return self.request.GET.get('post_login_redirect', reverse('admin:index'))


post_login_redirect = PostLoginRedirectView.as_view()
