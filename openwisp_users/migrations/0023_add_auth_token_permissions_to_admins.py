# Generated manually

from django.db import migrations

from openwisp_users.migrations import add_token_permissions_to_admins


class Migration(migrations.Migration):
    dependencies = [
        ("openwisp_users", "0022_user_expiration_date"),
    ]

    operations = [
        migrations.RunPython(
            add_token_permissions_to_admins, reverse_code=migrations.RunPython.noop
        )
    ]
