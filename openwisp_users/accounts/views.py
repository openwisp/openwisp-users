from allauth.account.forms import ChangePasswordForm as BaseChangePasswordForm
from allauth.account.views import PasswordChangeView as BasePasswordChangeView
from django import forms
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required


class ChangePasswordForm(BaseChangePasswordForm):
    next = forms.CharField(widget=forms.HiddenInput, required=False)


class PasswordChangeView(BasePasswordChangeView):
    form_class = ChangePasswordForm

    def get_success_url(self):
        if self.request.POST.get(REDIRECT_FIELD_NAME):
            return self.request.POST.get(REDIRECT_FIELD_NAME)
        return super().get_success_url()

    def get_initial(self):
        data = super().get_initial()
        data['next'] = self.request.GET.get(REDIRECT_FIELD_NAME)
        return data


password_change = login_required(PasswordChangeView.as_view())
