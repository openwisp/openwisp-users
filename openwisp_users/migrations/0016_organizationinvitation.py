# Generated by Django 4.0rc1 on 2021-11-26 00:17

import django.db.models.deletion
import django.utils.timezone
import organizations.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('openwisp_users', '0015_alter_organization_users_alter_organizationuser_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationInvitation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('guid', models.UUIDField(editable=False)),
                (
                    'invitee_identifier',
                    models.CharField(
                        help_text='The contact identifier for the invitee, email, phone number, social media handle, etc.',
                        max_length=1000,
                    ),
                ),
                (
                    'created',
                    organizations.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    'modified',
                    organizations.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    'invited_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)s_sent_invitations',
                        to='openwisp_users.user',
                    ),
                ),
                (
                    'invitee',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='%(app_label)s_%(class)s_invitations',
                        to='openwisp_users.user',
                    ),
                ),
                (
                    'organization',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='organization_invites',
                        to='openwisp_users.organization',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
