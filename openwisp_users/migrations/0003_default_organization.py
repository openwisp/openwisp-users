# Generated by Django 2.1.1 on 2018-09-16 12:20

from django.db import migrations

from openwisp_users.migrations import set_default_organization_uuid


class Migration(migrations.Migration):
    dependencies = [("openwisp_users", "0002_auto_20180508_2017")]

    operations = [
        migrations.RunPython(
            set_default_organization_uuid, reverse_code=migrations.RunPython.noop
        )
    ]
