from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from openwisp_users.multitenancy import (
    MultitenantAdminMixin,
    MultitenantOrgFilter,
    MultitenantRelatedOrgFilter,
)

from .models import Book, Config, Library, Shelf, Tag, Template


class BaseAdmin(MultitenantAdminMixin, admin.ModelAdmin):
    pass


class BookInline(admin.TabularInline):
    # Verify the parent mixin protects inlines that do not use it.
    model = Book
    fields = ["name", "author"]
    extra = 0


class ShelfAdmin(BaseAdmin):
    list_display = ["name", "organization"]
    list_filter = [MultitenantOrgFilter]
    fields = ["name", "organization", "tags", "created", "modified"]
    search_fields = ["name"]
    multitenant_shared_relations = ["tags"]
    inlines = [BookInline]


class ShelfFilter(MultitenantRelatedOrgFilter):
    field_name = "shelf"
    parameter_name = "shelf"
    title = _("Shelf")


class BookAdmin(BaseAdmin):
    list_display = ["name", "author", "organization", "shelf"]
    list_filter = [
        MultitenantOrgFilter,
        ShelfFilter,
    ]
    fields = ["name", "author", "organization", "shelf", "created", "modified"]
    autocomplete_fields = ["shelf"]
    multitenant_shared_relations = ["shelf"]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                "additional_buttons": [
                    {
                        "type": "button",
                        "url": "DUMMY",
                        "class": "previewbook",
                        "value": "Preview book",
                    },
                    {
                        "type": "button",
                        "url": "DUMMY",
                        "class": "downloadbook",
                        "value": "Download book",
                    },
                ]
            }
        )
        return super().change_view(request, object_id, form_url, extra_context)


class TemplateAdmin(BaseAdmin):
    pass


class TagAdmin(BaseAdmin):
    pass


class LibraryParentAdmin(MultitenantAdminMixin, admin.ModelAdmin):
    # Resolve the organization through Book for parent traversal coverage.
    multitenant_parent = "book"


class ConfigAdmin(BaseAdmin):
    # Exercise the write-protection opt-out through the admin endpoints.
    disabled_organization_write_protection = False
    fields = ["name", "organization", "template"]


admin.site.register(Shelf, ShelfAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Library, LibraryParentAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Config, ConfigAdmin)
