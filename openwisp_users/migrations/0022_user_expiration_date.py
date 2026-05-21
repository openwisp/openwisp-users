# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("openwisp_users", "0021_rename_user_id_email_openwisp_us_id_06c07a_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="expiration_date",
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text="Date on which the user account will expire.",
                null=True,
                verbose_name="expiration date",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["is_active", "expiration_date"], name="user_active_expiry_idx"
            ),
        ),
    ]
