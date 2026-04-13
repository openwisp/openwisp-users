from django.conf import settings

from openwisp_utils.utils import default_or_test

ORGANIZATION_USER_ADMIN = getattr(settings, "OPENWISP_ORGANIZATION_USER_ADMIN", True)
ORGANIZATION_OWNER_ADMIN = getattr(settings, "OPENWISP_ORGANIZATION_OWNER_ADMIN", True)
USERS_AUTH_API = getattr(settings, "OPENWISP_USERS_AUTH_API", True)
USERS_AUTH_THROTTLE_RATE = getattr(
    settings,
    "OPENWISP_USERS_AUTH_THROTTLE_RATE",
    default_or_test(value="20/day", test=None),
)
AUTH_BACKEND_AUTO_PREFIXES = getattr(
    settings, "OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES", tuple()
)


def _export_organizations(user):
    return ",".join(
        f'({org_id},{perm["is_admin"]})'
        for org_id, perm in user.organizations_dict.items()
    )


EXPORT_USERS_COMMAND_CONFIG = {
    "fields": [
        "id",
        "username",
        "email",
        "password",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "phone_number",
        "birth_date",
        "location",
        "notes",
        "language",
        {"name": "organizations", "callable": _export_organizations},
    ],
    "select_related": [],
    "prefetch_related": [],
}
USER_PASSWORD_EXPIRATION = getattr(
    settings, "OPENWISP_USERS_USER_PASSWORD_EXPIRATION", 0
)
STAFF_USER_PASSWORD_EXPIRATION = getattr(
    settings, "OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION", 0
)
# Set the AutocompleteFilter view if it is not defined in the settings
setattr(
    settings,
    "OPENWISP_AUTOCOMPLETE_FILTER_VIEW",
    getattr(
        settings,
        "OPENWISP_AUTOCOMPLETE_FILTER_VIEW",
        "openwisp_users.views.AutocompleteJsonView",
    ),
)

# if any OAuth/SAML provider is enabled, allow managing keys/secrets
SOCIALACCOUNT_ADMIN_NEEDED = getattr(
    settings,
    "OPENWISP_USERS_SOCIALACCOUNT_ADMIN_NEEDED",
    any(
        app.startswith("allauth.socialaccount.providers.")
        for app in settings.INSTALLED_APPS
    ),
)
