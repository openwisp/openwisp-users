# Manually Created
from django.db import migrations
from openwisp_users.migrations import update_admins_permissions
import swapper


class Migration(migrations.Migration):

    org_model = swapper.get_model_name('openwisp_users', 'organization')
    model_app_label = swapper.split(org_model)[0]
    dependencies = [
        (model_app_label, '0002_default_groups_and_permissions'),
    ]

    operations = [
        migrations.RunPython(
            update_admins_permissions, reverse_code=migrations.RunPython.noop
        ),
    ]
