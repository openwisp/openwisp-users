from allauth.account.forms import ChangePasswordForm as BaseChangePasswordForm
from allauth.account.views import PasswordChangeView as BasePasswordChangeView
from django import forms
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView


class ChangePasswordForm(BaseChangePasswordForm):
    next = forms.CharField(widget=forms.HiddenInput, required=False)


class PasswordChangeView(BasePasswordChangeView):
    form_class = ChangePasswordForm
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('account_change_password_success')

    def get_success_url(self):
        if self.request.POST.get(REDIRECT_FIELD_NAME):
            return self.request.POST.get(REDIRECT_FIELD_NAME)
        return super().get_success_url()

    def get_initial(self):
        data = super().get_initial()
        data['next'] = self.request.GET.get(REDIRECT_FIELD_NAME)
        return data


password_change = login_required(PasswordChangeView.as_view())
password_change_success = login_required(
    TemplateView.as_view(template_name='account/password_change_success.html')
)
