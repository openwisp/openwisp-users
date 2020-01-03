from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from .models import OrganizationUser, User


class MultitenantAdminMixin(object):
    """
    Mixin that makes a ModelAdmin class multitenant:
    users will see only the objects related to the organizations
    they are associated with.
    """
    multitenant_shared_relations = []
    multitenant_parent = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent = self.multitenant_parent
        shared_relations = self.multitenant_shared_relations
        if parent and parent not in shared_relations:
            self.multitenant_shared_relations.append(parent)

    def get_repr(self, obj):
        return str(obj)

    get_repr.short_description = _('name')

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
        if hasattr(self.model, 'organization'):
            return qs.filter(organization__in=user.organizations_pk)
        elif not self.multitenant_parent:
            return qs
        else:
            qsarg = '{0}__organization__in'.format(self.multitenant_parent)
            return qs.filter(**{qsarg: user.organizations_pk})

    def _edit_form(self, request, form):
        """
        Modifies the form querysets as follows;
        if current user is not superuser:
            * show only relevant organizations
            * show only relations associated to relevant organizations
              or shared relations
        else show everything
        """
        fields = form.base_fields
        if not request.user.is_superuser:
            orgs_pk = request.user.organizations_pk
            # organizations relation;
            # may be readonly and not present in field list
            if 'organization' in fields:
                org_field = fields['organization']
                org_field.queryset = org_field.queryset.filter(pk__in=orgs_pk)
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
        if not request.user.is_superuser:
            user = request.user
            org_users = OrganizationUser.objects.filter(user=user) \
                                                .select_related('organization')
            qs = User.objects.none()
            for org_user in org_users:
                if org_user.is_admin:
                    qs = qs | org_user.organization.users.all().distinct()
            # hide superusers from organization operators
            # so they can't edit nor delete them
            qs = qs.filter(is_superuser=False)
        else:
            qs = super().get_queryset(request)
        return qs


class MultitenantOrgFilter(admin.RelatedFieldListFilter):
    """
    Admin filter that shows only organizations the current
    user is associated with in its available choices
    """
    multitenant_lookup = 'pk__in'

    def field_choices(self, field, request, model_admin):
        if request.user.is_superuser:
            return super().field_choices(field, request, model_admin)
        organizations = request.user.organizations_pk
        return field.get_choices(include_blank=False,
                                 limit_choices_to={self.multitenant_lookup: organizations})


class MultitenantRelatedOrgFilter(MultitenantOrgFilter):
    """
    Admin filter that shows only objects which have a relation with
    one of the organizations the current user is associated with
    """
    multitenant_lookup = 'organization__in'
