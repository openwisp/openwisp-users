from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.management import create_permissions


def set_default_organization_uuid(apps, schema_editor):
    """
    Get or create a default organization then
    set settings._OPENWISP_DEFAULT_ORG_UUID
    """
    organization = apps.get_model('openwisp_users', 'organization')
    default_organization = organization.objects.first()
    if default_organization is None:
        default_organization = organization(
            name='default',
            slug='default',
            description='This is the default organization. '
            'It was created automatically during installation. '
            'You can simply rename it to your organization name.',
        )
        default_organization.full_clean()
        default_organization.save()

    # settings._OPENWISP_DEFAULT_ORG_UUID is used in
    # openwisp-radius.migrations, it helps to enable
    # users to migrate from freeradius 3
    settings._OPENWISP_DEFAULT_ORG_UUID = default_organization.pk


def create_default_groups(apps, schema_editor):
    group = apps.get_model('openwisp_users', 'group')

    # To populate all the permissions
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    operator = group.objects.filter(name='Operator')
    if operator.count() == 0:
        operator = group.objects.create(name='Operator')

    admin = group.objects.filter(name='Administrator')
    if admin.count() == 0:
        admin = group.objects.create(name='Administrator')
        permissions = [
            Permission.objects.get(
                content_type__app_label="openwisp_users", codename='add_user'
            ).pk,
            Permission.objects.get(
                content_type__app_label="openwisp_users", codename='change_user'
            ).pk,
            Permission.objects.get(
                content_type__app_label="openwisp_users",
                codename='change_organizationuser',
            ).pk,
            Permission.objects.get(
                content_type__app_label="openwisp_users",
                codename='delete_organizationuser',
            ).pk,
            Permission.objects.get(
                content_type__app_label="openwisp_users",
                codename='add_organizationuser',
            ).pk,
        ]
        try:
            permissions += [
                Permission.objects.get(
                    content_type__app_label="openwisp_users", codename='view_user'
                ).pk,
                Permission.objects.get(
                    content_type__app_label="openwisp_users", codename='view_group'
                ).pk,
                Permission.objects.get(
                    content_type__app_label="openwisp_users",
                    codename='view_organizationuser',
                ).pk,
            ]
        except Permission.DoesNotExist:
            pass
        admin.permissions.set(permissions)
