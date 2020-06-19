from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.management import create_permissions
import swapper


def set_default_organization_uuid(apps, schema_editor):
    """
    Get or create a default organization then
    set settings._OPENWISP_DEFAULT_ORG_UUID
    """
    org_model = swapper.get_model_name('openwisp_users', 'organization')
    model_app_label = swapper.split(org_model)[0]
    organization = apps.get_model(model_app_label, 'organization')
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
    org_model = swapper.get_model_name('openwisp_users', 'organization')
    model_app_label = swapper.split(org_model)[0]
    group = apps.get_model(model_app_label, 'group')

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
                content_type__app_label=model_app_label, codename='add_user'
            ).pk,
            Permission.objects.get(
                content_type__app_label=model_app_label, codename='change_user'
            ).pk,
            Permission.objects.get(
                content_type__app_label=model_app_label,
                codename='change_organizationuser',
            ).pk,
            Permission.objects.get(
                content_type__app_label=model_app_label,
                codename='delete_organizationuser',
            ).pk,
            Permission.objects.get(
                content_type__app_label=model_app_label,
                codename='add_organizationuser',
            ).pk,
        ]
        try:
            permissions += [
                Permission.objects.get(
                    content_type__app_label=model_app_label, codename='view_user'
                ).pk,
                Permission.objects.get(
                    content_type__app_label=model_app_label, codename='view_group'
                ).pk,
                Permission.objects.get(
                    content_type__app_label=model_app_label,
                    codename='view_organizationuser',
                ).pk,
            ]
        except Permission.DoesNotExist:
            pass
        admin.permissions.set(permissions)
