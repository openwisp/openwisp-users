from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache


@method_decorator(never_cache)
def patched_admin_login(self, request, extra_context=None):
    """
    This method is adapted from 'django.contrib.admin.sites.AdminSite.login'
    which does not respect the REDIRECT_LOGIN_URL setting.
    Thus, the 'login' method is patched to redirect the logged
    in user to '/accounts/post_login_redirect/' for password
    expiration check.
    """
    if request.method == "GET" and self.has_permission(request):
        # Already logged-in, redirect to admin index
        index_path = reverse("admin:index", current_app=self.name)
        return HttpResponseRedirect(index_path)

    # Since this module gets imported in the application's root package,
    # it cannot import models from other applications at the module level,
    # and django.contrib.admin.forms eventually imports User.
    from django.contrib.admin.forms import AdminAuthenticationForm

    # OpenWISP customization begins
    from .accounts.utils import StaffUserPasswordExpirationLoginView as LoginView

    # OpenWISP customization ends

    context = {
        **self.each_context(request),
        "title": _("Log in"),
        "subtitle": None,
        "app_path": request.get_full_path(),
        "username": request.user.get_username(),
    }
    if (
        REDIRECT_FIELD_NAME not in request.GET
        and REDIRECT_FIELD_NAME not in request.POST
    ):
        context[REDIRECT_FIELD_NAME] = reverse("admin:index", current_app=self.name)
    context.update(extra_context or {})

    defaults = {
        "extra_context": context,
        "authentication_form": self.login_form or AdminAuthenticationForm,
        "template_name": self.login_template or "admin/login.html",
    }
    request.current_app = self.name
    return LoginView.as_view(**defaults)(request)
