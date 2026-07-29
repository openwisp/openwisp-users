from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.template import loader

from openwisp_utils.admin_theme.email import send_email

User = get_user_model()


class PasswordResetForm(BasePasswordResetForm):
    """
    Sends the reset e-mail through openwisp-utils' themed ``send_email``
    instead of Django's stock mail templates.
    """

    def get_users(self, email):
        """
        Given an email, return matching user who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent users with unusable passwords from resetting their password.
        """
        users = User.objects.filter(email__iexact=email, is_active=True)
        return [user for user in users if user.has_usable_password()]

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.txt",
        text_template_name=None,
        use_https=False,
        token_generator=None,
        request=None,
        extra_email_context=None,
        url_generator=None,
        **kwargs,
    ):
        if token_generator is None:
            # Must match the token generator dj-rest-auth's
            # PasswordResetConfirmSerializer uses to validate the token
            # (allauth.account.forms.default_token_generator when allauth
            # is installed), otherwise every confirm request is rejected.
            if "allauth" in settings.INSTALLED_APPS:
                from allauth.account.forms import default_token_generator
            else:
                from django.contrib.auth.tokens import default_token_generator
            token_generator = default_token_generator

        if extra_email_context is None:
            extra_email_context = {}
        if not domain_override:
            domain_override = request.get_host() if request else "example.com"
        site_name = domain_override.split(":")[0]
        for user in self.get_users(self.cleaned_data["email"]):
            token = token_generator.make_token(user)
            context = {
                "email": user.email,
                "user": user,
                "uid": user_pk_to_url_str(user),
                "user_id": user.id,
                "token": token,
                "site_name": site_name,
                "site": domain_override,
                "protocol": "https" if use_https else "http",
            }
            if url_generator:
                context["call_to_action_url"] = url_generator(request, user, token)
            context.update(extra_email_context)
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                user.email,
                text_template_name=text_template_name,
            )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        to_email,
        text_template_name=None,
    ):
        """
        Send the password reset email.

        ``openwisp_utils.admin_theme.email.send_email`` always sends from
        ``settings.DEFAULT_FROM_EMAIL`` and has no override hook, so this
        form does not accept a ``from_email`` argument.
        """
        subject = context.get("subject")
        if not subject:
            subject_text = loader.render_to_string(subject_template_name, context)
            subject = "".join(subject_text.splitlines())
        body_html = loader.render_to_string(email_template_name, context)
        # strip_tags() only parses entity-like "&word" sequences when the
        # value contains angle brackets: rendering a tag-free plain-text
        # template keeps URLs with query strings (e.g. "&token=...") intact,
        # instead of being mangled into "&token;=..." by strip_tags().
        body_text = (
            loader.render_to_string(text_template_name, context)
            if text_template_name
            else body_html
        )
        send_email(subject, body_text, body_html, [to_email], context)
