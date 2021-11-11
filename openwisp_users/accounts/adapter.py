from allauth.account.adapter import DefaultAccountAdapter
from django.utils.translation import gettext as _
from openwisp_utils.admin_theme import settings as utils_settings


class EmailAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        context['logo_url'] = utils_settings.OPENWISP_EMAIL_LOGO
        site_name = context['current_site'].name
        context['subject'] = _('Welcome to %(site_name)s') % {'site_name': site_name}
        context['message'] = _('Thank you for using <b>%(site_name)s</b>') % {
            'site_name': site_name
        }
        context['call_to_action_url'] = context['activate_url']
        context['call_to_action_text'] = _('Confirm')
        super().send_mail(template_prefix, email, context)
