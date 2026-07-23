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
    # opt-out hook: set to False on subclasses that should allow writes
    # to objects belonging to a disabled organization
    disabled_organization_write_protection = True

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
            return qs.filter(organization__in=user.organizations_managed)
        if self.model.__name__ == "Organization":
            return qs.filter(pk__in=user.organizations_managed)
        elif not self.multitenant_parent:
            return qs
        else:
            qsarg = "{0}__organization__in".format(self.multitenant_parent)
            return qs.filter(**{qsarg: user.organizations_managed})

    def _get_object_organization(self, obj):
        """
        Returns the organization an object belongs to, traversing
        ``multitenant_parent`` for models whose organization is reached
        through a parent (e.g. a Book through its Shelf).
        """
        organization = getattr(obj, "organization", None)
        if organization is None and self.multitenant_parent:
            parent = obj
            for attr in self.multitenant_parent.split("__"):
                parent = getattr(parent, attr, None)
                if parent is None:
                    break
            organization = getattr(parent, "organization", None)
        return organization

    def has_change_permission(self, request, obj=None):
        """
        Objects belonging to a disabled organization stay readable and
        deletable, but cannot be changed, regardless of the user being a
        superuser. Subclasses can opt out with
        ``disabled_organization_write_protection = False``.
        """
        if self.disabled_organization_write_protection and obj is not None:
            organization = self._get_object_organization(obj)
            if organization is not None and not organization.is_active:
                return False
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request, *args, **kwargs):
        """
        Hide the Add button from admins who manage no active organization:
        the organization dropdown would be empty and the form could never be
        submitted. Does not apply to the user admin or to models without an
        organization (directly or through ``multitenant_parent``).

        ``*args`` keeps this compatible with both ``ModelAdmin``
        (``request``) and ``InlineModelAdmin`` (``request, obj``), since this
        mixin is used on inlines too.
        """
        if (
            not request.user.is_superuser
            and self.model != User
            and not request.user.organizations_managed
        ):
            # Any model with an organization field (directly, or reached
            # through multitenant_parent) is blocked: _edit_form() makes the
            # field required for non-superusers, so the form could not be
            # submitted without an active organization to pick anyway.
            if hasattr(self.model, "organization") or self.multitenant_parent:
                return False
        return super().has_add_permission(request, *args, **kwargs)

    def _edit_form(self, request, form, obj=None):
        """
        Modifies the form querysets as follows;
        if current user is not superuser:
            * show only relevant organizations
            * show only relations associated to relevant organizations
              or shared relations
            * do not allow organization field to be empty (shared org)
        else show everything
        Organization choices always exclude disabled organizations,
        superusers included, except an admin that opted out of write
        protection (``disabled_organization_write_protection = False``)
        keeps the edited object's own disabled organization selectable,
        or the form could never be saved.
        """
        fields = form.base_fields
        user = request.user
        org_field = fields.get("organization")
        keep_disabled_org_pk = None
        if not self.disabled_organization_write_protection and obj is not None:
            organization = self._get_object_organization(obj)
            if organization is not None and not organization.is_active:
                keep_disabled_org_pk = organization.pk
        if org_field:
            allowed = Q(is_active=True)
            if keep_disabled_org_pk is not None:
                allowed |= Q(pk=keep_disabled_org_pk)
            org_field.queryset = org_field.queryset.filter(allowed)
        if user.is_superuser and org_field and not org_field.required:
            org_field.empty_label = SHARED_SYSTEMWIDE_LABEL
        elif not user.is_superuser:
            orgs_pk = user.organizations_managed
            # organizations relation;
            # may be readonly and not present in field list
            if org_field:
                managed = Q(pk__in=orgs_pk)
                if keep_disabled_org_pk is not None:
                    managed |= Q(pk=keep_disabled_org_pk)
                org_field.queryset = org_field.queryset.filter(managed)
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
        self._edit_form(request, form, obj)
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
    widget_attrs.update({"data-empty-label": SHARED_SYSTEMWIDE_LABEL})


class MultitenantRelatedOrgFilter(MultitenantOrgFilter):
    """
    Admin filter that shows only objects which have a relation with
    one of the organizations the current user is associated with
    """

    org_lookup = "organization__in"
