from allauth.account.models import EmailAddress
from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from organizations.base_admin import (BaseOrganizationAdmin,
                                      BaseOrganizationOwnerAdmin,
                                      BaseOrganizationUserAdmin,
                                      BaseOwnerInline)

from .base import BaseAdmin
from .models import (Group, Organization, OrganizationOwner, OrganizationUser,
                     User)


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
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        # only super users can be created without organization
        form.empty_permitted = self.instance.is_superuser
        return form


class OrganizationUserInline(admin.StackedInline):
    model = OrganizationUser
    formset = RequiredInlineFormSet

    def get_extra(self, request, obj=None, **kwargs):
        if not obj:
            return 1
        return 0


class EmailRequiredMixin(forms.ModelForm):
    email = forms.EmailField(label=_('Email'), max_length=254, required=True)

    def _clean_email(self, email):
        if User.objects.filter(email=email).count() > 0 or \
         EmailAddress.objects.filter(email=email).exclude(user=self.instance.pk).count() > 0:
            raise ValidationError({'email': ['User with this email already exists.']})

    def clean(self):
        cleaned_data = super(EmailRequiredMixin, self).clean()
        if 'email' in self.changed_data:
            self._clean_email(email=cleaned_data.get('email'))
        return cleaned_data


class UserCreationForm(EmailRequiredMixin, BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        fields = ['username', 'email', 'password1', 'password2', 'is_staff']
        fields_superuser = fields[:] + ['is_superuser']
        fieldsets = (
            (None, {
                'classes': ('wide',),
                'fields': fields,
            }),
        )
        fieldsets_superuser = (
            (None, {
                'classes': ('wide',),
                'fields': fields_superuser,
            }),
        )

    class Media:
        js = ('openwisp-users/js/addform.js',)


class UserChangeForm(EmailRequiredMixin, BaseUserChangeForm):
    pass


class UserAdmin(BaseUserAdmin, BaseAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    readonly_fields = ['last_login', 'date_joined']
    list_display = ['username',
                    'email',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'date_joined',
                    'last_login']
    inlines = [EmailAddressInline, OrganizationUserInline]
    save_on_top = True

    def get_fieldsets(self, request, obj=None):
        # add form fields for staff users
        if not obj and not request.user.is_superuser:
            return self.add_form.Meta.fieldsets
        # add form fields for superusers
        if not obj and request.user.is_superuser:
            return self.add_form.Meta.fieldsets_superuser
        return super(UserAdmin, self).get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        # retrieve readonly fields
        fields = super(UserAdmin, self).get_readonly_fields(request, obj)
        # do not allow operators to escalate their privileges
        if not request.user.is_superuser:
            # copy to avoid modifying reference
            fields = fields[:] + ['is_superuser', 'user_permissions']
        return fields

    def has_change_permission(self, request, obj=None):
        # do not allow operators to edit details of superusers
        # returns 403 if trying to access the change form of a superuser
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super(UserAdmin, self).has_change_permission(request, obj)

    def get_queryset(self, request):
        # if not superuser, show only members of the same org
        if not request.user.is_superuser:
            user = request.user
            org_users = OrganizationUser.objects.filter(user=user) \
                                                .select_related('organization')
            qs = None
            for org_user in org_users:
                add_qs = org_user.organization.users.all()
                if qs:
                    # if merging an existing queryset
                    # avoid including the current user twice
                    qs = qs | add_qs.exclude(pk=user.id)
                else:
                    qs = add_qs
                # hide superusers from organization operators
                # so they can't edit nor delete them
                qs = qs.filter(is_superuser=False)
        else:
            qs = super(UserAdmin, self).get_queryset(request)
        return qs

    def get_inline_instances(self, request, obj=None):
        """
        Avoid displaying inline objects when adding a new user
        """
        if obj:
            return super(UserAdmin, self).get_inline_instances(request, obj)
        inline = OrganizationUserInline(self.model, self.admin_site)
        if request:
            if hasattr(inline, '_has_add_permission'):
                has_add_perm = inline._has_add_permission(request, obj)
            else:
                has_add_perm = inline.has_add_permission(request)
            if has_add_perm:
                return [inline]
        return []

    def save_model(self, request, obj, form, change):
        """
        Automatically creates email addresses for users
        added/changed via the django-admin interface
        """
        super(UserAdmin, self).save_model(request, obj, form, change)
        if obj.email:
            EmailAddress.objects.add_email(request,
                                           user=obj,
                                           email=obj.email,
                                           confirm=True,
                                           signup=True)


base_fields = list(UserAdmin.fieldsets[1][1]['fields'])
additional_fields = ['bio', 'url', 'company', 'location']
UserAdmin.fieldsets[1][1]['fields'] = base_fields + additional_fields
UserAdmin.add_fieldsets[0][1]['fields'] = ('username', 'email', 'password1', 'password2')


class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    pass


class OwnerInline(BaseOwnerInline):
    model = OrganizationOwner


class OrganizationAdmin(BaseOrganizationAdmin, BaseAdmin):
    view_on_site = False
    inlines = [OwnerInline]


class OrganizationUserAdmin(BaseOrganizationUserAdmin, BaseAdmin):
    view_on_site = False


class OrganizationOwnerAdmin(BaseOrganizationOwnerAdmin, BaseAdmin):
    list_display = ('get_user', 'organization')

    def get_user(self, obj):
        return obj.organization_user.user


admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationUser, OrganizationUserAdmin)
admin.site.register(OrganizationOwner, OrganizationOwnerAdmin)
# unregister auth.Group
base_group_model = apps.get_model('auth', 'Group')
admin.site.unregister(base_group_model)
# register openwisp_users.Group proxy model
admin.site.register(Group, GroupAdmin)

# unregister some admin components to keep the admin interface simple
# we can re-enable these models later when they will be really needed
for model in [('account', 'EmailAddress'),
              ('socialaccount', 'SocialApp'),
              ('socialaccount', 'SocialToken'),
              ('socialaccount', 'SocialAccount')]:
    admin.site.unregister(apps.get_model(*model))
