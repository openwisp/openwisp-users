import logging
from copy import deepcopy

from allauth import app_settings as allauth_settings
from allauth.account.models import EmailAddress
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from organizations.base_admin import (
    BaseOrganizationAdmin,
    BaseOrganizationOwnerAdmin,
    BaseOrganizationUserAdmin,
)
from organizations.exceptions import OwnershipRequired
from phonenumber_field.formfields import PhoneNumberField
from swapper import load_model

from openwisp_utils.admin import CopyableFieldsAdmin

from . import settings as app_settings
from .multitenancy import MultitenantAdminMixin, MultitenantOrgFilter
from .utils import BaseAdmin

Group = load_model("openwisp_users", "Group")
Organization = load_model("openwisp_users", "Organization")
OrganizationOwner = load_model("openwisp_users", "OrganizationOwner")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
User = get_user_model()
logger = logging.getLogger(__name__)


def user_not_allowed_to_change_owner(user, obj):
    return (
        obj
        and not user.is_superuser
        and user.pk != obj.pk
        and obj.is_owner_of_any_organization
    )


class EmailAddressInline(admin.StackedInline):
    model = EmailAddress
    extra = 0
    readonly_fields = ["email"]

    def has_add_permission(self, *args, **kwargs):
        """
        Do not let admins add new email objects via inlines
        in order to not mess the coherence of the database.
        Admins can still change the main email field of the User model,
        that will automatically add a new email address object and
        send a confirmation email, see ``UserAdmin.save_model``
        """
        return False

    def has_change_permission(self, request, obj=None):
        if user_not_allowed_to_change_owner(request.user, obj):
            self.can_delete = False
            return False
        return super().has_change_permission(request, obj)


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


class OrganizationOwnerInline(admin.StackedInline):
    model = OrganizationOwner
    extra = 0
    autocomplete_fields = ("organization_user",)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and not request.user.is_owner(obj):
            return False
        return super().has_change_permission(request, obj)


class OrganizationUserInline(admin.StackedInline):
    model = OrganizationUser
    formset = RequiredInlineFormSet
    view_on_site = False
    fields = ("organization", "is_admin")
    autocomplete_fields = ("organization",)

    def get_formset(self, request, obj=None, **kwargs):
        """
        In form dropdowns, display only organizations
        in which operator `is_admin` and for superusers
        display all organizations
        """
        formset = super().get_formset(request, obj=obj, **kwargs)
        if request.user.is_superuser:
            return formset
        if not request.user.is_superuser:
            formset.form.base_fields["organization"].queryset = (
                Organization.objects.filter(pk__in=request.user.organizations_managed)
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
            self.readonly_fields = ["is_admin"]
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if user_not_allowed_to_change_owner(request.user, obj):
            return False
        return super().has_change_permission(request, obj)


class UserFormMixin(forms.ModelForm):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True)

    def validate_user_groups(self, data):
        is_staff = data.get("is_staff")
        is_superuser = data.get("is_superuser")
        groups = data.get("groups")
        if is_staff and not is_superuser and not groups:
            raise ValidationError(
                {"groups": _("A staff user must belong to a group, please select one.")}
            )

    def clean(self):
        cleaned_data = super().clean()
        self.validate_user_groups(cleaned_data)
        return cleaned_data


class UserCreationForm(UserFormMixin, BaseUserCreationForm):
    phone_number = PhoneNumberField(widget=forms.TextInput(), required=False)

    class Meta(BaseUserCreationForm.Meta):
        model = User
        basic_fields = ["username", "email", "password1", "password2"]
        fields = basic_fields + ["expiration_date"]
        personal_fields = ["first_name", "last_name", "phone_number", "birth_date"]
        fieldsets = (
            (None, {"classes": ("wide",), "fields": basic_fields}),
            (
                _("Account expiration"),
                {"classes": ("wide",), "fields": ("expiration_date",)},
            ),
            (_("Personal Info"), {"classes": ("wide",), "fields": personal_fields}),
            (
                _("Permissions"),
                {"classes": ("wide",), "fields": ["is_active", "is_staff", "groups"]},
            ),
        )
        fieldsets_superuser = (
            (None, {"classes": ("wide",), "fields": basic_fields}),
            (
                _("Account expiration"),
                {"classes": ("wide",), "fields": ("expiration_date",)},
            ),
            (_("Personal Info"), {"classes": ("wide",), "fields": personal_fields}),
            (
                _("Permissions"),
                {
                    "classes": ("wide",),
                    "fields": ["is_active", "is_staff", "is_superuser", "groups"],
                },
            ),
        )

    class Media:
        js = ("admin/js/jquery.init.js", "openwisp-users/js/addform.js")


class UserChangeForm(UserFormMixin, BaseUserChangeForm):
    pass


class UserAdmin(MultitenantAdminMixin, BaseUserAdmin, BaseAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ["-date_joined"]
    readonly_fields = ["last_login", "date_joined", "password_updated"]
    list_display = [
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    ]
    inlines = [EmailAddressInline, OrganizationUserInline]
    save_on_top = True
    actions = ["delete_selected_overridden", "make_inactive", "make_active"]
    fieldsets = list(BaseUserAdmin.fieldsets)

    # To ensure extended apps use this template.
    change_form_template = "admin/openwisp_users/user/change_form.html"

    class Media:
        css = {"all": ("openwisp-users/css/admin.css",)}

    def require_confirmation(func):
        """
        Decorator to lead to a confirmation page.
        This has been used rather than simply adding the same lines
        in action functions inorder to avoid repetition of the same
        lines in the two added actions and more actions
        incase they are added in future.
        """

        def wrapper(modeladmin, request, queryset):
            opts = modeladmin.model._meta
            if request.POST.get("confirmation") is None:
                request.current_app = modeladmin.admin_site.name
                context = {
                    **modeladmin.admin_site.each_context(request),
                    "title": _("Are you sure?"),
                    "action": request.POST["action"],
                    "queryset": queryset,
                    "opts": opts,
                }
                return TemplateResponse(
                    request, "admin/action_confirmation.html", context
                )
            return func(modeladmin, request, queryset)

        wrapper.__name__ = func.__name__
        return wrapper

    @admin.action(
        description=_("Flag selected users as inactive"), permissions=["change"]
    )
    @require_confirmation
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        count = queryset.count()
        if count:
            self.message_user(
                request,
                _("Successfully made %(count)d %(model_name)s inactive.")
                % {
                    "count": count,
                    "model_name": model_ngettext(self.opts, count),
                },
                messages.SUCCESS,
            )

    @admin.action(
        description=_("Flag selected users as active"), permissions=["change"]
    )
    @require_confirmation
    def make_active(self, request, queryset):
        # Clear past expiration dates before reactivating users.
        today = localdate()
        queryset = queryset.filter(is_active=False)
        expired_count = queryset.filter(expiration_date__lt=today).update(
            is_active=True, expiration_date=None
        )
        count = queryset.filter(
            Q(expiration_date__isnull=True) | Q(expiration_date__gte=today)
        ).update(is_active=True)
        count += expired_count
        if count:
            message = _("Successfully activated %(count)d %(model_name)s") % {
                "count": count,
                "model_name": model_ngettext(self.opts, count),
            }
            if expired_count:
                message = " ".join(
                    [
                        message,
                        ngettext(
                            "and cleared %(count)d expiration date.",
                            "and cleared %(count)d expiration dates.",
                            expired_count,
                        )
                        % {"count": expired_count},
                    ]
                )
            else:
                message = f"{message}."
            self.message_user(
                request,
                message,
                messages.SUCCESS,
            )

    def get_list_display(self, request):
        """
        Hide `is_superuser` from column from operators
        """
        default_list_display = super().get_list_display(request)
        if not request.user.is_superuser and "is_superuser" in default_list_display:
            # avoid editing the default_list_display
            operators_list_display = default_list_display[:]
            operators_list_display.remove("is_superuser")
            return operators_list_display
        return default_list_display

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if not request.user.is_superuser and "is_superuser" in filters:
            # hide is_superuser filter for non-superusers
            operators_filter_list = list(filters)
            operators_filter_list.remove("is_superuser")
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
            user_permissions = ("is_active", "is_staff", "groups", "user_permissions")
            # copy to avoid modifying reference
            non_superuser_fieldsets = deepcopy(fieldsets)
            for fieldset in non_superuser_fieldsets:
                fields = fieldset[1].get("fields", ())
                if "is_superuser" in fields:
                    fieldset[1]["fields"] = user_permissions
                    break
            return non_superuser_fieldsets
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        # retrieve readonly fields
        fields = super().get_readonly_fields(request, obj)
        # do not allow operators to escalate their privileges
        if not request.user.is_superuser:
            # copy to avoid modifying reference
            fields = fields[:] + ["user_permissions", "is_superuser"]
        return fields

    def has_change_permission(self, request, obj=None):
        if user_not_allowed_to_change_owner(request.user, obj):
            return False
        # do not allow operators to edit details of superusers
        # returns 403 if trying to access the change form of a superuser
        if (
            obj and obj.is_superuser and not request.user.is_superuser
        ):  # pragma: no cover
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if user_not_allowed_to_change_owner(request.user, obj):
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.POST.get("post") and "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description=delete_selected.short_description, permissions=["delete"])
    def delete_selected_overridden(self, request, queryset):
        if not request.user.is_superuser:
            users_pk = queryset.values_list("pk", flat=True)
            owners_list = list(
                OrganizationOwner.objects.filter(organization_user__user__in=users_pk)
                .select_related("organization_user__user")
                .values_list("organization_user__user__username", flat=True)
            )
            owners = ", ".join(owners_list)
            excluded_owners_qs = queryset.exclude(username__in=owners_list)
            # if trying to delete any owner, show an error message
            count = len(owners_list)
            if count:
                self.message_user(
                    request,
                    ngettext(
                        "Can't delete %(count)d organization owner: %(owners)s",
                        "Can't delete %(count)d organization owners: %(owners)s",
                        count,
                    )
                    % {"count": count, "owners": owners},
                    messages.ERROR,
                )
            # if trying to delete only owners, stop here
            if queryset.exists() and not excluded_owners_qs.exists():
                redirect_url = reverse(
                    f"admin:{self.model._meta.app_label}_user_changelist"
                )
                return HttpResponseRedirect(redirect_url)
            # otherwise proceed but remove owners from the delete queryset
            else:
                queryset = excluded_owners_qs
        return delete_selected(self, request, queryset)

    def get_inline_instances(self, request, obj=None):
        """
        1. Avoid displaying inline objects when adding a new user
        2. Make OrganizationUserInline readonly for non-superuser
        """
        if obj:
            inlines = super().get_inline_instances(request, obj).copy()
            if not request.user.is_superuser:
                for inline in inlines:
                    if isinstance(inline, OrganizationUserInline):
                        orguser_index = inlines.index(inline)
                        inlines.remove(inline)
                        orguser_readonly = OrganizationUserInlineReadOnly(
                            self.model, self.admin_site
                        )
                        inlines.insert(orguser_index, orguser_readonly)
                        break
            return inlines
        inline = OrganizationUserInline(self.model, self.admin_site)
        if request:
            if hasattr(inline, "_has_add_permission"):
                has_add_perm = inline._has_add_permission(request, obj)
            else:
                has_add_perm = inline.has_add_permission(request, obj)
            if has_add_perm:
                return [inline]
        return []

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj is not None and user_not_allowed_to_change_owner(request.user, obj):
            show_owner_warning = True
            extra_context.update({"show_owner_warning": show_owner_warning})
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
                    "Got exception {} while sending "
                    "verification email to user {}, email {}".format(
                        type(e), obj.username, obj.email
                    )
                )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        not_deleted = 0
        for obj in formset.deleted_objects:
            try:
                obj.delete()
            except OwnershipRequired:
                not_deleted += 1
        if not_deleted:
            self.message_user(
                request,
                ngettext(
                    "Can't delete %(count)d organization user because it "
                    "belongs to an organization owner.",
                    "Can't delete %(count)d organization users because they "
                    "belong to some organization owners.",
                    not_deleted,
                )
                % {"count": not_deleted},
                messages.ERROR,
            )
        for instance in instances:
            instance.save()


class OrganizationUserFilter(MultitenantOrgFilter):
    """
    Allows filtering users by the organization they're related to
    """

    field_name = f"{Organization._meta.app_label}_organization"

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(
                openwisp_users_organizationuser__organization=self.value()
            )
        return queryset


base_fields = list(UserAdmin.fieldsets[1][1]["fields"])
additional_fields = ["bio", "url", "company", "location", "phone_number", "birth_date"]
UserAdmin.fieldsets[1][1]["fields"] = base_fields + additional_fields
UserAdmin.fieldsets.insert(
    1, (_("Account expiration"), {"fields": ("expiration_date",)})
)
UserAdmin.fieldsets.insert(4, (_("Internal"), {"fields": ("notes",)}))
primary_fields = list(UserAdmin.fieldsets[0][1]["fields"])
UserAdmin.fieldsets[0][1]["fields"] = primary_fields + ["password_updated"]
UserAdmin.add_fieldsets[0][1]["fields"] = (
    "username",
    "email",
    "password1",
    "password2",
)
UserAdmin.search_fields += ("phone_number",)
UserAdmin.list_filter = (OrganizationUserFilter,) + UserAdmin.list_filter


class GroupAdmin(BaseGroupAdmin, BaseAdmin):
    if "reversion" in settings.INSTALLED_APPS:
        # Correctly register the proxy model
        def reversion_register(self, model, **kwargs):
            return super().reversion_register(model, for_concrete_model=False, **kwargs)


class OrganizationAdmin(
    MultitenantAdminMixin, BaseOrganizationAdmin, BaseAdmin, CopyableFieldsAdmin
):
    view_on_site = False
    # this inline has an autocomplete field pointing to OrganizationUserAdmin
    if app_settings.ORGANIZATION_USER_ADMIN and app_settings.ORGANIZATION_OWNER_ADMIN:
        inlines = [OrganizationOwnerInline]
    readonly_fields = ["uuid", "created", "modified"]
    ordering = ["name"]
    list_display = ["name", "is_active", "created", "modified"]
    copyable_fields = ("uuid",)

    def get_inline_instances(self, request, obj=None):
        """
        Remove OrganizationOwnerInline from organization add form
        """
        inlines = super().get_inline_instances(request, obj).copy()
        if not obj:
            for inline in inlines:
                if isinstance(inline, OrganizationOwnerInline):
                    inlines.remove(inline)
                    break
        return inlines

    def has_change_permission(self, request, obj=None):
        """
        Allow only managers and superuser to change organization
        """
        if obj and not request.user.is_superuser and not request.user.is_manager(obj):
            return False
        return super().has_change_permission(request, obj)

    class Media(CopyableFieldsAdmin.Media):
        css = {"all": ("openwisp-users/css/admin.css",)}


class OrganizationUserAdmin(
    MultitenantAdminMixin, BaseOrganizationUserAdmin, BaseAdmin
):
    view_on_site = False
    actions = ["delete_selected_overridden"]
    fields = ("user", "organization", "is_admin")
    search_fields = ["user__username", "organization__name"]

    def get_readonly_fields(self, request, obj=None):
        # retrieve readonly fields
        fields = super().get_readonly_fields(request, obj)
        # do not allow operators to escalate their privileges
        if not request.user.is_superuser:
            # copy to avoid modifying reference
            fields = ["is_admin"]
        return fields

    def has_delete_permission(self, request, obj=None):
        """
        operators should not delete organization users of organizations
        where they are not admins
        """
        if request.user.is_superuser:
            return True
        if obj and not request.user.is_manager(obj.organization):
            return False
        return super().has_delete_permission(request, obj)

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except OwnershipRequired:
            self.message_user(
                request,
                _(
                    "Can't delete this organization user because "
                    "it belongs to an organization owner."
                ),
                messages.ERROR,
            )
            redirect_url = reverse(
                f"admin:{self.model._meta.app_label}_organizationuser_change",
                args=[object_id],
            )
            return HttpResponseRedirect(redirect_url)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.POST.get("post") and "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description=delete_selected.short_description, permissions=["delete"])
    def delete_selected_overridden(self, request, queryset):
        count = 0
        pks = []
        for obj in queryset:
            if obj.user.is_owner(obj.organization_id):
                pks.append(obj.pk)
                count += 1
        # if trying to delete only org users which belong to owners, stop here
        if count and count == queryset.count():
            self.message_user(
                request,
                _("Can't delete organization users which belong to owners."),
                messages.ERROR,
            )
            redirect_url = reverse(
                f"admin:{self.model._meta.app_label}_organizationuser_changelist"
            )
            return HttpResponseRedirect(redirect_url)
        # if some org owners' org users were selected
        if count and count != queryset.count():
            queryset = queryset.exclude(pk__in=pks)
            self.message_user(
                request,
                ngettext(
                    "Can't delete %(count)d organization user because it "
                    "belongs to an organization owner.",
                    "Can't delete %(count)d organization users because they "
                    "belong to some organization owners.",
                    count,
                )
                % {"count": count},
                messages.ERROR,
            )
        # otherwise proceed but remove org users from the delete queryset
        return delete_selected(self, request, queryset)


class OrganizationOwnerAdmin(
    MultitenantAdminMixin, BaseOrganizationOwnerAdmin, BaseAdmin
):
    list_display = ("get_user", "organization")
    if app_settings.ORGANIZATION_USER_ADMIN and app_settings.ORGANIZATION_OWNER_ADMIN:
        autocomplete_fields = ["organization_user", "organization"]

    def get_user(self, obj):
        return obj.organization_user.user


admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)

# OrganizationUser items can be managed on the user page
if app_settings.ORGANIZATION_USER_ADMIN:
    admin.site.register(OrganizationUser, OrganizationUserAdmin)
# this item is not being used right now
if app_settings.ORGANIZATION_OWNER_ADMIN:
    admin.site.register(OrganizationOwner, OrganizationOwnerAdmin)

# unregister auth.Group
base_group_model = apps.get_model("auth", "Group")
admin.site.unregister(base_group_model)
# register openwisp_users.Group proxy model
admin.site.register(Group, GroupAdmin)

# unregister some admin components to keep the admin interface simple
# we can re-enable these models later when they will be really needed
EmailAddress = apps.get_model("account", "EmailAddress")
if admin.site.is_registered(EmailAddress):
    admin.site.unregister(EmailAddress)

# authtoken's admin registers TokenProxy when its admin module is imported.
# Depending on the INSTALLED_APPS order, openwisp_users.admin may load before
# authtoken.admin, so the unregister below would find TokenProxy not yet
# registered and skip it. Force the import here so TokenProxy is always
# registered first and the unregister always takes effect.
from rest_framework.authtoken import admin as authtoken_admin  # noqa

user_app_label = get_user_model()._meta.app_label
ApiKey = apps.get_model(user_app_label, "ApiKey")
TokenProxy = apps.get_model("authtoken", "TokenProxy")
API_KEY_MASK = "*" * 40

if admin.site.is_registered(TokenProxy):
    admin.site.unregister(TokenProxy)


# Keep the token primary key out of the DOM because it is the raw API key.
class NonRenderingHiddenInput(forms.HiddenInput):
    def render(self, name, value, attrs=None, renderer=None):
        return ""


class ApiKeyInlineForm(forms.ModelForm):
    generate_token = forms.BooleanField(label=_("Create new API key"), required=False)

    class Meta:
        model = ApiKey
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["generate_token"].widget = forms.HiddenInput()

    def clean_generate_token(self):
        if self.instance.pk:
            return False
        return self.cleaned_data.get("generate_token", False)


class ApiKeyInlineFormSet(BaseInlineFormSet):
    def __init__(
        self,
        data=None,
        files=None,
        instance=None,
        save_as_new=False,
        prefix=None,
        queryset=None,
        **kwargs,
    ):
        prefix = prefix or self.get_default_prefix()
        # max_num=1 keeps the existing token form at index 0.
        if data is not None and instance and hasattr(instance, "auth_token"):
            data = data.copy()
            data[f"{prefix}-0-key"] = instance.auth_token.key
        super().__init__(
            data=data,
            files=files,
            instance=instance,
            save_as_new=save_as_new,
            prefix=prefix,
            queryset=queryset,
            **kwargs,
        )

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields[self._pk_field.name].widget = NonRenderingHiddenInput()


class ApiKeyInline(admin.StackedInline):
    model = ApiKey
    form = ApiKeyInlineForm
    formset = ApiKeyInlineFormSet
    extra = 0
    max_num = 1
    readonly_fields = ("api_key", "created")

    def get_fields(self, request, obj=None):
        if obj and hasattr(obj, "auth_token"):
            return ("api_key", "created")
        return ("generate_token",)

    @admin.display(description=_("API key"))
    def api_key(self, obj):
        parent_obj = getattr(self, "parent_obj", None)
        value = (
            obj.key
            if parent_obj and parent_obj.pk == self.request.user.pk
            else API_KEY_MASK
        )
        return format_html(
            '<input type="text" readonly aria-label="{}" '
            'class="vTextField" value="{}">',
            _("API key"),
            value,
        )

    def get_formset(self, request, obj=None, **kwargs):
        self.request = request
        self.parent_obj = obj
        return super().get_formset(request, obj=obj, **kwargs)

    def get_queryset(self, request):
        """
        Let users see and manage their own API key without holding the
        API key permissions. The base inline ``get_queryset`` forces an
        empty queryset when ``has_view_or_change_permission`` is False, and
        that check receives no object, so the self-account exception in the
        permission methods cannot apply there. On the user's own page we
        therefore return the real queryset and skip that gate, while other
        users' pages keep the default permission based filtering.
        """
        parent_obj = getattr(self, "parent_obj", None)
        if parent_obj and parent_obj.pk == request.user.pk:
            queryset = self.model._default_manager.get_queryset()
            ordering = self.get_ordering(request)
            if ordering:
                queryset = queryset.order_by(*ordering)
            return queryset
        return super().get_queryset(request)

    def _is_self(self, request, obj):
        """Whether the authenticated user is viewing/editing his own account."""
        return bool(obj and obj.pk == request.user.pk)

    def has_view_permission(self, request, obj=None):
        return self._is_self(request, obj) or super().has_view_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._is_self(request, obj) or super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_self(request, obj) or super().has_delete_permission(request)


UserAdmin.inlines.insert(1, ApiKeyInline)


if allauth_settings.SOCIALACCOUNT_ENABLED:
    _unregister_socialaccount_models = [
        ("socialaccount", "SocialToken"),
        ("socialaccount", "SocialAccount"),
    ]
    # allauth OAuth/SAML not enabled
    if not app_settings.SOCIALACCOUNT_ADMIN_NEEDED:  # pragma: no cover
        _unregister_socialaccount_models.append(("socialaccount", "SocialApp"))
    # allauth OAuth/SAML enabled
    else:
        from allauth.socialaccount.models import SocialAccount

        class SocialAccountInline(admin.StackedInline):
            model = SocialAccount
            extra = 0
            readonly_fields = ("provider", "uid", "extra_data")

            def has_add_permission(self, request, obj=None):
                return False

            def has_delete_permission(self, request, obj=None):
                return False

        UserAdmin.inlines.append(SocialAccountInline)

    # Un-register cluttering socialaccount models
    for model in _unregister_socialaccount_models:
        model_class = apps.get_model(*model)
        if admin.site.is_registered(model_class):
            admin.site.unregister(model_class)
