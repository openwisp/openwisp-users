from allauth.account.adapter import DefaultAccountAdapter
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from openwisp_utils.admin_theme.email import send_email


class EmailAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        site_name = context['current_site'].name
        subject = _('Welcome to %(site_name)s') % {'site_name': site_name}
        try:
            template_name = '{0}_message.txt'.format(template_prefix)
            body_text = render_to_string(template_name, context, self.request).strip()
        except TemplateDoesNotExist:
            body_text = ''
        template_name = '{0}_message.html'.format(template_prefix)
        body_html = render_to_string(template_name, context, self.request).strip()
        context["footer"] = _("Thank you for using %(site_name)s") % {
            "site_name": site_name
        }
        context['call_to_action_url'] = context['activate_url']
        context['call_to_action_text'] = _('Confirm')
        send_email(subject, body_text, body_html, [email], context)
