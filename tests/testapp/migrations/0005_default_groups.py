# Manually Created

from django.db import migrations
from testapp.migrations import update_administrator_permissions


class Migration(migrations.Migration):
    dependencies = [
        ('testapp', '0004_library'),
    ]

    operations = [
        migrations.RunPython(
            update_administrator_permissions, reverse_code=migrations.RunPython.noop
        ),
    ]
