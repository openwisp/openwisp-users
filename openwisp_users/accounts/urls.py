"""
allauth proxy urls
limits the available URLs of django-all auth
in order to keep sign up related features
disabled (not implemented yet).
"""

from importlib import import_module

from allauth import app_settings
from allauth.account import views
from allauth.socialaccount import providers
from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

redirect_view = RedirectView.as_view(url=reverse_lazy('admin:index'))


urlpatterns = [
    url(r"^signup/$", redirect_view, name="account_signup"),
    url(r"^login/$", views.login, name="account_login"),
    url(r"^logout/$", views.logout, name="account_logout"),
    url(r"^inactive/$", views.account_inactive, name="account_inactive"),
    # E-mail
    url(
        r"^confirm-email/$",
        views.email_verification_sent,
        name="account_email_verification_sent",
    ),
    url(
        r"^confirm-email/(?P<key>[-:\w]+)/$",
        views.confirm_email,
        name="account_confirm_email",
    ),
    # password reset
    url(r"^password/reset/$", views.password_reset, name="account_reset_password"),
    url(
        r"^password/reset/done/$",
        views.password_reset_done,
        name="account_reset_password_done",
    ),
    url(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    url(
        r"^password/reset/key/done/$",
        views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
    url(
        r"^email-verification-success/",
        TemplateView.as_view(template_name='account/email_verification_success.html'),
        name='email_confirmation_success',
    ),
]

if app_settings.SOCIALACCOUNT_ENABLED:
    urlpatterns += [url(r'^social/', include('allauth.socialaccount.urls'))]

for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns
