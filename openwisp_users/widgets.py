from django.contrib.admin.widgets import AutocompleteSelect as BaseAutocompleteSelect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class OrganizationAutocompleteSelect(BaseAutocompleteSelect):
    class Media:
        js = ['admin/js/jquery.init.js', 'openwisp-users/js/org-autocomplete.js']

    def get_url(self):
        return reverse('admin:ow-auto-filter')

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value is None:
            # Organization is None when the object is shared
            # between all organizations. Therefore, we add
            # an option here to be used by select2.
            context['widget']['optgroups'][0][1].append(
                {
                    'attrs': {'selected': True},
                    'index': '1',
                    'label': _('Shared systemwide (no organization)'),
                    'name': 'organization',
                    'selected': 'null',
                    'template_name': 'django/forms/widgets/select_option.html',
                    'type': 'select',
                    'value': 'null',
                    'wrap_label': True,
                }
            )
        return context
