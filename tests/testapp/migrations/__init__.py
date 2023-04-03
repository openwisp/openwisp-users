import swapper
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q


def update_administrator_permissions(apps, schema_editor):
    model_name = swapper.get_model_name('openwisp_users', 'Group')
    model_label = swapper.split(model_name)[0]
    Group = apps.get_model(model_label, 'Group')

    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    try:
        operator = Group.objects.get(name='Administrator')
        permissions = Permission.objects.filter(
            Q(codename__endswith='template')
            | Q(codename__endswith='shelf')
            | Q(codename__endswith='book')
            | Q(codename__endswith='tag')
        ).values_list('pk', flat=True)
        operator.permissions.add(*permissions)
    except ObjectDoesNotExist:
        pass
