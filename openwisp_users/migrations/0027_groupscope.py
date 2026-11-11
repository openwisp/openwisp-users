import django.db.models.deletion
import swapper
from django.db import migrations, models


def populate_group_scopes(apps, schema_editor):
    Group = apps.get_model("openwisp_users", "Group")
    GroupScope = apps.get_model("openwisp_users", "GroupScope")
    for group in Group.objects.all():
        GroupScope.objects.get_or_create(
            group=group, defaults={"assignable_to": "everyone"}
        )


class Migration(migrations.Migration):

    dependencies = [
        ("openwisp_users", "0026_user_password_based_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupScope",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "assignable_to",
                    models.CharField(
                        choices=[
                            ("everyone", "Globally to everyone"),
                            ("superusers", "Only to superusers"),
                            ("organizations", "Only to specified organizations"),
                        ],
                        default="everyone",
                        help_text=(
                            "Defines who can assign this group to users: "
                            "globally to everyone, only to superusers, "
                            "or only to specified organizations."
                        ),
                        max_length=16,
                        verbose_name="assignable to",
                    ),
                ),
                (
                    "group",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scope",
                        to=swapper.get_model_name("openwisp_users", "Group"),
                        verbose_name="group",
                    ),
                ),
                (
                    "organizations",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "Organizations whose managers can assign this group "
                            "(only applies when set to 'Only to specified organizations')."
                        ),
                        related_name="assignable_groups",
                        to=swapper.get_model_name("openwisp_users", "Organization"),
                        verbose_name="organizations",
                    ),
                ),
            ],
            options={
                "verbose_name": "group scope",
                "verbose_name_plural": "group scopes",
                "abstract": False,
                "swappable": swapper.swappable_setting("openwisp_users", "GroupScope"),
            },
        ),
        migrations.RunPython(
            populate_group_scopes, reverse_code=migrations.RunPython.noop
        ),
    ]
