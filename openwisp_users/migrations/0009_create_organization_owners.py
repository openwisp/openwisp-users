# Generated by Django 3.0.8 on 2020-07-08 15:10

from django.db import migrations

from . import create_organization_owners


class Migration(migrations.Migration):

    dependencies = [
        ('openwisp_users', '0008_update_admins_permissions'),
    ]

    operations = [migrations.RunPython(create_organization_owners)]
