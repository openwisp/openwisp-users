import inspect

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.messages import warning
from django.core.exceptions import PermissionDenied
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.debug import sensitive_variables
from openwisp_utils.admin_theme.email import send_email

from ..backends import UsersAllowExpiredPassBackend
from ..exceptions import UserPasswordExpired


@sensitive_variables("credentials")
def authenticate(request=None, **credentials):
    """
    If the given credentials are valid, return a User object.
    """
    backend = UsersAllowExpiredPassBackend()
    backend_signature = inspect.signature(backend.authenticate)
    try:
        backend_signature.bind(request, **credentials)
    except TypeError:
        return django_authenticate(request, **credentials)
    try:
        user = backend.authenticate(request, **credentials)
    except PermissionDenied:
        return
    except UserPasswordExpired as error:
        user = error.user
        warning(
            request,
            'Your password has expired, please update your password at {url}'.format(
                url=request.build_absolute_uri(reverse('account_change_password'))
            ),
        )
    if not user:
        return
    user.backend = 'openwisp_users.backends.UsersAllowExpiredPassBackend'
    return user


class EmailAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        subject = render_to_string("{0}_subject.txt".format(template_prefix), context)
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)
        content = {}
        errors = {}
        for ext in ['html', 'txt']:
            template_name = '{0}_message.{1}'.format(template_prefix, ext)
            if 'activate_url' in context:
                context['call_to_action_url'] = context['activate_url']
                context['call_to_action_text'] = _('Confirm')
            try:
                template_name = '{0}_message.{1}'.format(template_prefix, ext)
                content[ext] = render_to_string(
                    template_name, context, self.request
                ).strip()
            except TemplateDoesNotExist as e:
                errors[ext] = e
            text = content.get('txt', '')
            html = content.get('html', '')
            # both templates fail to load, raise the exception
            if len(errors.keys()) >= 2:
                raise errors['txt'] from errors['html']
        send_email(subject, text, html, [email], context)

    def authenticate(self, request, **credentials):
        """
        This method has been adapted from
        'allauth.account.adapter.DefaultAccountAdapter'
        to use the "authenticate" method defined in this file.
        """
        from allauth.account.auth_backends import AuthenticationBackend

        self.pre_authenticate(request, **credentials)
        AuthenticationBackend.unstash_authenticated_user()
        user = authenticate(request, **credentials)
        alt_user = AuthenticationBackend.unstash_authenticated_user()
        user = user or alt_user
        if user and allauth_settings.LOGIN_ATTEMPTS_LIMIT:
            self._delete_login_attempts_cached_email(request, **credentials)
        else:
            self.authentication_failed(request, **credentials)
        return user
