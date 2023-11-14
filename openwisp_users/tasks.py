from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.sites.models import Site
from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.utils.translation import gettext_lazy as _
from openwisp_utils.admin_theme.email import send_email

from . import settings as app_settings

User = get_user_model()


@shared_task
def password_expiration_email():
    """
    Notify users whose password is expiring in exactly 7 days.
    """
    if (
        not app_settings.USER_PASSWORD_EXPIRATION
        and not app_settings.STAFF_USER_PASSWORD_EXPIRATION
    ):
        # The password expiration feature is not enabled
        return
    expiry_date = now().date() + timedelta(days=7)
    query = Q()
    if app_settings.USER_PASSWORD_EXPIRATION:
        query |= Q(
            is_staff=False,
            password_updated=expiry_date
            - timedelta(days=app_settings.USER_PASSWORD_EXPIRATION),
        )
    if app_settings.STAFF_USER_PASSWORD_EXPIRATION:
        query |= Q(
            is_staff=True,
            password_updated=expiry_date
            - timedelta(days=app_settings.STAFF_USER_PASSWORD_EXPIRATION),
        )
    current_site = Site.objects.get_current()
    qs = (
        User.objects.exclude(
            # Exclude users having unusable password
            password__startswith=UNUSABLE_PASSWORD_PREFIX,
        )
        .filter(
            emailaddress__verified=True,
        )
        .filter(query)
    )
    for user in qs.iterator():
        send_email(
            subject=_('Your password is about to expire'),
            body_text=_('Your password is about to expire in 7 days'),
            body_html=_('You password is about to expire in 7 days.'),
            recipients=[user.email],
            extra_context={
                'call_to_action_url': 'https://{0}{1}'.format(
                    current_site.domain,
                    reverse('account_change_password'),
                ),
                'call_to_action_text': _('Change password'),
            },
        )
