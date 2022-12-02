from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from openwisp_users.multitenancy import (
    MultitenantAdminMixin,
    MultitenantOrgFilter,
    MultitenantRelatedOrgFilter,
)

from .models import Book, Library, Shelf, Template


class BaseAdmin(MultitenantAdminMixin, admin.ModelAdmin):
    pass


class ShelfAdmin(BaseAdmin):
    list_display = ['name', 'organization']
    list_filter = [MultitenantOrgFilter]
    fields = ['name', 'organization', 'created', 'modified']
    search_fields = ['name']


class ShelfFilter(MultitenantRelatedOrgFilter):
    field_name = 'shelf'
    parameter_name = 'shelf'
    title = _('Shelf')


class BookAdmin(BaseAdmin):
    list_display = ['name', 'author', 'organization', 'shelf']
    list_filter = [
        MultitenantOrgFilter,
        ShelfFilter,
    ]
    fields = ['name', 'author', 'organization', 'shelf', 'created', 'modified']
    multitenant_shared_relations = ['shelf']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                'additional_buttons': [
                    {
                        'type': 'button',
                        'url': 'DUMMY',
                        'class': 'previewbook',
                        'value': 'Preview book',
                    },
                    {
                        'type': 'button',
                        'url': 'DUMMY',
                        'class': 'downloadbook',
                        'value': 'Download book',
                    },
                ]
            }
        )
        return super().change_view(request, object_id, form_url, extra_context)


class TemplateAdmin(BaseAdmin):
    pass


admin.site.register(Shelf, ShelfAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Library)
