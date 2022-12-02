from openwisp_utils.admin_theme.views import (
    AutocompleteJsonView as BaseAutocompleteJsonView,
)
from swapper import load_model

Organization = load_model('openwisp_users', 'Organization')


class AutocompleteJsonView(BaseAutocompleteJsonView):
    def get_source_field_filter(self):
        """
        Fetches the ModelAdmin class of the source_field.model.
        Loops over all filter classes of ModelAdmin and
        returns filter with matching field_name.
        """
        source_model_admin = self.admin_site._registry[self.source_field.model]
        for filter in source_model_admin.list_filter:
            if getattr(filter, 'field_name', None) == self.source_field.name:
                return filter

    def get_org_lookup(self):
        if hasattr(self.source_field_filter, 'org_lookup'):
            return self.source_field_filter.org_lookup

    def get_queryset(self):
        self.source_field_filter = self.get_source_field_filter()
        qs = super().get_queryset()
        org_lookup = self.get_org_lookup()
        if not self.request.user.is_superuser and org_lookup:
            return qs.filter(**{org_lookup: self.request.user.organizations_managed})
        return qs
