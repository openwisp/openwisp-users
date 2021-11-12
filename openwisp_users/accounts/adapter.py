from allauth.account.adapter import DefaultAccountAdapter
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from openwisp_utils.admin_theme.email import send_email


class EmailAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        site_name = context['current_site'].name
        subject = render_to_string("{0}_subject.txt".format(template_prefix), context)
        subject = " ".join(subject.splitlines()).strip()
        subject = f'{site_name}: {subject}'
        for ext in ['html', 'txt']:
            try:
                template_name = '{0}_message.{1}'.format(template_prefix, ext)
                if ext == 'html':
                    body_html = render_to_string(
                        template_name, context, self.request
                    ).strip()
                    if 'activate_url' in context:
                        context['call_to_action_url'] = context['activate_url']
                        context['call_to_action_text'] = _('Confirm')
                else:
                    body_text = render_to_string(
                        template_name, context, self.request
                    ).strip()
            except TemplateDoesNotExist:
                if ext == 'txt':
                    if body_html == '':
                        raise
                    body_text = ''
                else:
                    body_html = ''
        send_email(subject, body_text, body_html, [email], context)
