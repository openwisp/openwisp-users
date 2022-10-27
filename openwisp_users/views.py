from openwisp_utils.admin_theme.views import (
    AutocompleteJsonView as BaseAutocompleteJsonView,
)
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')


class AutocompleteJsonView(BaseAutocompleteJsonView):
    def get_queryset(self):
        qs = super().get_queryset()
        if issubclass(self.model_admin.model, Organization):
            qs.filter(id__in=self.request.user.organizations_managed)
        return qs
