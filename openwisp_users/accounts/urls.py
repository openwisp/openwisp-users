"""
allauth proxy urls
limits the available URLs of django-all auth
in order to keep sign up related features
disabled (not implemented yet).
"""

from allauth.account import views
from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

redirect_view = RedirectView.as_view(url=reverse_lazy('admin:index'))


urlpatterns = [
    url(r"^signup/$", redirect_view, name="account_signup"),
    url(r"^login/$", views.login, name="account_login"),

    # E-mail
    url(r"^confirm-email/$", views.email_verification_sent,
        name="account_email_verification_sent"),
    url(r"^confirm-email/(?P<key>[-:\w]+)/$", views.confirm_email,
        name="account_confirm_email"),

    # password reset
    url(r"^password/reset/$", views.password_reset,
        name="account_reset_password"),
    url(r"^password/reset/done/$", views.password_reset_done,
        name="account_reset_password_done"),
    url(r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        views.password_reset_from_key,
        name="account_reset_password_from_key"),
    url(r"^password/reset/key/done/$", views.password_reset_from_key_done,
        name="account_reset_password_from_key_done"),
]
