import logging
from copy import deepcopy

from allauth import app_settings as allauth_settings
from allauth.account.models import EmailAddress
from django import forms
from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.forms.models import BaseInlineFormSet
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from openwisp_utils.admin import UUIDAdmin
from organizations.base_admin import (
    BaseOrganizationAdmin,
    BaseOrganizationOwnerAdmin,
    BaseOrganizationUserAdmin,
)

from . import settings as app_settings
from .base import BaseAdmin
from .models import Group, Organization, OrganizationOwner, OrganizationUser, User
from .multitenancy import MultitenantAdminMixin

logger = logging.getLogger(__name__)


class EmailAddressInline(admin.StackedInline):
    model = EmailAddress
    extra = 0
    readonly_fields = ['email']

    def has_add_permission(self, *args, **kwargs):
        """
        Do not let admins add new email objects via inlines
        in order to not mess the coherence of the database.
        Admins can still change the main email field of the User model,
        that will automatically add a new email address object and
        send a confirmation email, see ``UserAdmin.save_model``
        """
        return False


class RequiredInlineFormSet(BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super()._construct_form(i, **kwargs)
        # only super users can be created without organization
        form.empty_permitted = self.instance.is_superuser
        return form


class OrganizationUserInline(admin.StackedInline):
    model = OrganizationUser
    formset = RequiredInlineFormSet
    view_on_site = False

    def get_formset(self, request, obj=None, **kwargs):
        """
        In form dropdowns, display only organizations
        in which operator `is_admin` and for superusers
        display all organizations
        """
        formset = super().get_formset(request, obj=obj, **kwargs)
        if request.user.is_superuser:
            return formset
        if not request.user.is_superuser and not obj:
            operator_orgs = OrganizationUser.objects.values_list('organization').filter(
                user=request.user, is_admin=True
            )
            formset.form.base_fields[
                'organization'
            ].queryset = Organization.objects.filter(pk__in=operator_orgs)
        if not request.user.is_superuser and obj:
            formset.form.base_fields[
                'organization'
            ].queryset = Organization.objects.filter(
                pk__in=request.user.organizations_pk
            )
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        if not obj:
            return 1
        return 0


class OrganizationUserInlineReadOnly(OrganizationUserInline):
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            self.readonly_fields = ['is_admin']
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class EmailRequiredMixin(forms.ModelForm):
    email = forms.EmailField(label=_('Email'), max_length=254, required=True)


class UserCreationForm(EmailRequiredMixin, BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        fields = ['username', 'email', 'password1', 'password2', 'is_staff']
        fields_superuser = fields[:] + ['is_superuser']
        fieldsets = ((None, {'classes': ('wide',), 'fields': fields}),)
        fieldsets_superuser = (
            (None, {'classes': ('wide',), 'fields': fields_superuser}),
        )

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'openwisp-users/js/addform.js',
        )


class UserChangeForm(EmailRequiredMixin, BaseUserChangeForm):
    pass


class UserAdmin(MultitenantAdminMixin, BaseUserAdmin, BaseAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ['-date_joined']
    readonly_fields = ['last_login', 'date_joined']
    list_display = [
        'username',
        'email',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login',
    ]
    inlines = [EmailAddressInline, OrganizationUserInline]
    save_on_top = True
    actions = ['make_inactive', 'make_active']

    def require_confirmation(func):
        """
        Decorator to lead to a confirmation page.
        This has been used rather than simply adding the same lines in action functions
        inorder to avoid repetition of the same lines in the two added actions and more actions
        incase they are added in future.
        """

        def wrapper(modeladmin, request, queryset):
            opts = modeladmin.model._meta
            if request.POST.get('confirmation') is None:
                request.current_app = modeladmin.admin_site.name
                context = {
                    'action': request.POST['action'],
                    'queryset': queryset,
                    'opts': opts,
                }
                return TemplateResponse(
                    request, 'admin/action_confirmation.html', context
                )
            return func(modeladmin, request, queryset)

        wrapper.__name__ = func.__name__
        return wrapper

    @require_confirmation
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        count = queryset.count()
        if count:
            self.message_user(
                request,
                _(
                    f'Successfully made {count} {model_ngettext(self.opts, count)} inactive.'
                ),
                messages.SUCCESS,
            )

    make_inactive.short_description = _('Flag selected users as inactive')

    @require_confirmation
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        count = queryset.count()
        if count:
            self.message_user(
                request,
                _(
                    f'Successfully made {count} {model_ngettext(self.opts, count)} active.'
                ),
                messages.SUCCESS,
            )

    make_active.short_description = _('Flag selected users as active')

    def get_list_display(self, request):
        """
        Hide `is_superuser` from column from operators
        """
        default_list_display = super().get_list_display(request)
        if not request.user.is_superuser and 'is_superuser' in default_list_display:
            # avoid editing the default_list_display
            operators_list_display = default_list_display[:]
            operators_list_display.remove('is_superuser')
            return operators_list_display
        return default_list_display

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if not request.user.is_superuser and 'is_superuser' in filters:
            # hide is_superuser filter for non-superusers
            operators_filter_list = list(filters)
            operators_filter_list.remove('is_superuser')
            return tuple(operators_filter_list)
        return filters

    def get_fieldsets(self, request, obj=None):
        # add form fields for staff users
        if not obj and not request.user.is_superuser:
            return self.add_form.Meta.fieldsets
        # add form fields for superusers
        if not obj and request.user.is_superuser:
            return self.add_form.Meta.fieldsets_superuser
        # return fieldsets according to user
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            # edit this tuple to add / remove permission items
            # visible to non-superusers
            user_permissions = ('is_active', 'is_staff', 'groups', 'user_permissions')
            # copy to avoid modifying reference
            non_superuser_fieldsets = deepcopy(fieldsets)
            non_superuser_fieldsets[2][1]['fields'] = user_permissions
            return non_superuser_fieldsets
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        # retrieve readonly fields
        fields = super().get_readonly_fields(request, obj)
        # do not allow operators to escalate their privileges
        if not request.user.is_superuser:
            # copy to avoid modifying reference
            fields = fields[:] + ['user_permissions']
        return fields

    def has_change_permission(self, request, obj=None):
        # do not allow operators to edit details of superusers
        # returns 403 if trying to access the change form of a superuser
        if (
            obj and obj.is_superuser and not request.user.is_superuser
        ):  # pragma: no cover
            return False
        return super().has_change_permission(request, obj)

    def get_inline_instances(self, request, obj=None):
        """
        Avoid displaying inline objects when adding a new user
        """
        if obj:
            return super().get_inline_instances(request, obj)
        inline = OrganizationUserInline(self.model, self.admin_site)
        if request:
            if hasattr(inline, '_has_add_permission'):
                has_add_perm = inline._has_add_permission(request, obj)
            else:
                has_add_perm = inline.has_add_permission(request, obj)
            if has_add_perm:
                return [inline]
        return []

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not request.user.is_superuser:
            self.inlines[1] = OrganizationUserInlineReadOnly
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        """
        Automatically creates email addresses for users
        added/changed via the django-admin interface
        """
        super().save_model(request, obj, form, change)
        if obj.email:
            try:
                EmailAddress.objects.add_email(
                    request, user=obj, email=obj.email, confirm=True, signup=True
                )
            except Exception as e:
                logger.exception(
                    'Got exception {} while sending '
                    'verification email to user {}, email {}'.format(
                        type(e), obj.username, obj.email
                    )
                )


base_fields = list(UserAdmin.fieldsets[1][1]['fields'])
additional_fields = ['bio', 'url', 'company', 'location', 'phone_number']
UserAdmin.fieldsets[1][1]['fields'] = base_fields + additional_fields
UserAdmin.add_fieldsets[0][1]['fields'] = (
    'username',
    'email',
    'password1',
    'password2',
)
UserAdmin.search_fields += ('phone_number',)


class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    pass


class OrganizationAdmin(BaseOrganizationAdmin, BaseAdmin, UUIDAdmin):
    view_on_site = False
    inlines = []
    readonly_fields = ['uuid']
    ordering = ['name']

    def has_change_permission(self, request, obj=None):
        """
        Allow operator to change an organization only if
        they is an admin of that organization
        """
        if obj and not request.user.is_superuser:
            try:
                org = OrganizationUser.objects.get(organization=obj, user=request.user)
                if not org.is_admin:
                    return False
            except OrganizationUser.DoesNotExist:
                pass
        return super().has_change_permission(request, obj)

    class Media(UUIDAdmin.Media):
        css = {'all': ('openwisp-users/css/admin.css',)}


class OrganizationUserAdmin(
    MultitenantAdminMixin, BaseOrganizationUserAdmin, BaseAdmin
):
    view_on_site = False

    def get_readonly_fields(self, request, obj=None):
        # retrieve readonly fields
        fields = super().get_readonly_fields(request, obj)
        # do not allow operators to escalate their privileges
        if not request.user.is_superuser:
            # copy to avoid modifying reference
            fields = ['is_admin']
        return fields

    def has_delete_permission(self, request, obj=None):
        """
        operators should not delete organization users of organizations
        where they are not admins
        """
        if request.user.is_superuser:
            return True
        if obj:
            operator_org = OrganizationUser.objects.get(
                organization=obj.organization, user=request.user
            )
            if operator_org.is_admin:
                return True
            else:
                return False


class OrganizationOwnerAdmin(
    MultitenantAdminMixin, BaseOrganizationOwnerAdmin, BaseAdmin,
):
    list_display = ('get_user', 'organization')

    def get_user(self, obj):
        return obj.organization_user.user


admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)

# OrganizationUser items can be managed on the user page
if app_settings.ORGANIZATON_USER_ADMIN:
    admin.site.register(OrganizationUser, OrganizationUserAdmin)
# this item is not being used right now
if app_settings.ORGANIZATON_OWNER_ADMIN:
    admin.site.register(OrganizationOwner, OrganizationOwnerAdmin)

# unregister auth.Group
base_group_model = apps.get_model('auth', 'Group')
admin.site.unregister(base_group_model)
# register openwisp_users.Group proxy model
admin.site.register(Group, GroupAdmin)

# unregister some admin components to keep the admin interface simple
# we can re-enable these models later when they will be really needed
admin.site.unregister(apps.get_model('account', 'EmailAddress'))
if allauth_settings.SOCIALACCOUNT_ENABLED:
    for model in [
        ('socialaccount', 'SocialApp'),
        ('socialaccount', 'SocialToken'),
        ('socialaccount', 'SocialAccount'),
    ]:
        admin.site.unregister(apps.get_model(*model))
