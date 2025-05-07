from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from swapper import load_model

from openwisp_utils.admin_theme.filters import AutocompleteFilter

from .widgets import SHARED_SYSTEMWIDE_LABEL, OrganizationAutocompleteSelect

User = get_user_model()
OrganizationUser = load_model("openwisp_users", "OrganizationUser")


class MultitenantAdminMixin(object):
    """
    Mixin that makes a ModelAdmin class multitenant:
    users will see only the objects related to the organizations
    they are associated with.
    """

    multitenant_shared_relations = None
    multitenant_parent = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent = self.multitenant_parent
        shared_relations = self.multitenant_shared_relations or []
        # copy to avoid modifying class attribute
        shared_relations = list(shared_relations)
        # add multitenant_parent to multitenant_shared_relations if necessary
        if parent and parent not in shared_relations:
            shared_relations.append(parent)
        self.multitenant_shared_relations = shared_relations

    def get_repr(self, obj):
        return str(obj)

    get_repr.short_description = _("name")

    def get_queryset(self, request):
        """
        If current user is not superuser, show only the
        objects associated to organizations he/she is associated with
        """
        qs = super().get_queryset(request)
        user = request.user
        if self.model == User:
            return self.multitenant_behaviour_for_user_admin(request)
        if user.is_superuser:
            return qs
        if hasattr(self.model, "organization"):
            return qs.filter(
                Q(organization__in=user.organizations_managed) | Q(organization=None)
            )
        if self.model.__name__ == "Organization":
            return qs.filter(pk__in=user.organizations_managed)
        elif not self.multitenant_parent:
            return qs
        else:
            qsarg = f"{self.multitenant_parent}__organization"
            return qs.filter(
                Q(**{f"{qsarg}__in": user.organizations_managed}) | Q(**{qsarg: None})
            )

    def _has_org_permission(self, request, obj, perm_func):
        """
        Helper method to check object-level permissions for users
        associated with specific organizations.
        """
        perm = perm_func(request, obj)
        if obj and self.multitenant_parent:
            # In case of a multitenant parent, we need to check if the
            # user has permission on the parent object.
            obj = getattr(obj, self.multitenant_parent)
        if not request.user.is_superuser and obj and hasattr(obj, "organization_id"):
            perm = perm and (
                obj.organization_id
                and str(obj.organization_id) in request.user.organizations_managed
            )
        return perm

    def has_change_permission(self, request, obj=None):
        """
        Returns True if the user has permission to change the object.
        Non-superusers cannot change shared objects.
        """
        return self._has_org_permission(request, obj, super().has_change_permission)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the user has permission to delete the object.
        Non-superusers cannot change shared objects.
        """
        return self._has_org_permission(request, obj, super().has_delete_permission)

    def _edit_form(self, request, form):
        """
        Modifies the form querysets as follows;
        if current user is not superuser:
            * show only relevant organizations
            * show only relations associated to relevant organizations
              or shared relations
            * do not allow organization field to be empty (shared org)
        else show everything
        """
        fields = form.base_fields
        user = request.user
        org_field = fields.get("organization")
        if user.is_superuser and org_field and not org_field.required:
            org_field.empty_label = SHARED_SYSTEMWIDE_LABEL
        elif not user.is_superuser:
            orgs_pk = user.organizations_managed
            # organizations relation;
            # may be readonly and not present in field list
            if org_field:
                org_field.queryset = org_field.queryset.filter(pk__in=orgs_pk)
                org_field.empty_label = None
                org_field.required = True
            # other relations
            q = Q(organization__in=orgs_pk) | Q(organization=None)
            for field_name in self.multitenant_shared_relations:
                # each relation may be readonly
                # and not present in field list
                if field_name not in fields:
                    continue
                field = fields[field_name]
                field.queryset = field.queryset.filter(q)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        self._edit_form(request, form)
        return form

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj=None, **kwargs)
        self._edit_form(request, formset.form)
        return formset

    def multitenant_behaviour_for_user_admin(self, request):
        """
        if operator is logged in - show only users
        from same organization and hide superusers
        if superuser is logged in - show all users
        """
        user = request.user
        qs = super().get_queryset(request)
        if user.is_superuser:
            return qs
        # Instead of querying the User model using the many-to-many relation
        # openwisp_users__organizationuser__organization, a separate query is
        # made to fetch users of organizations managed by the logged-in user.
        # This approach avoids duplicate objects for users that are admin of
        # multiple organizations managed by the logged-in user.
        # See https://github.com/openwisp/openwisp-users/issues/324.
        # We cannot use .distinct() on the User query directly, because
        # it causes issues when performing delete action from the admin.
        user_ids = (
            OrganizationUser.objects.filter(
                organization_id__in=user.organizations_managed
            )
            .values_list("user_id")
            .distinct()
        )
        # hide superusers from organization operators
        # so they can't edit nor delete them
        return qs.filter(id__in=user_ids, is_superuser=False)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organization":
            kwargs["widget"] = OrganizationAutocompleteSelect(
                db_field, self.admin_site, using=kwargs.get("using")
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MultitenantOrgFilter(AutocompleteFilter):
    """
    Admin filter that shows only organizations the current
    user is associated with in its available choices
    """

    field_name = "organization"
    parameter_name = "organization"
    org_lookup = "id__in"
    title = _("organization")
    widget_attrs = AutocompleteFilter.widget_attrs.copy()
    widget_attrs.update(
        {"data-empty-label": SHARED_SYSTEMWIDE_LABEL, "data-is-filter": "true"}
    )


class MultitenantRelatedOrgFilter(MultitenantOrgFilter):
    """
    Admin filter that shows only objects which have a relation with
    one of the organizations the current user is associated with
    """

    org_lookup = "organization__in"
