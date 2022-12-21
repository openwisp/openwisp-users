from django.contrib.admin.widgets import AutocompleteSelect as BaseAutocompleteSelect
from django.urls import reverse


class OrganizationAutocompleteSelect(BaseAutocompleteSelect):
    class Media:
        js = ['admin/js/jquery.init.js', 'openwisp-users/js/org-autocomplete.js']

    def get_url(self):
        return reverse('admin:ow-auto-filter')
