from django.db import migrations, models


class Migration(migrations.Migration):
    """
    0021_rename_user_id_email_openwisp_us_id_06c07a_idx used RenameIndex with
    old_fields=, which added a second "user_id_email_idx" state entry instead
    of renaming the one added by 0006_id_email_index_together (which already
    had that exact name). The database was never affected, only one index
    has ever existed there, but the duplicated migration state makes any
    later SQLite table rebuild try to CREATE INDEX it twice and crash with
    "index user_id_email_idx already exists". This migration is state-only:
    it removes both duplicate entries and adds back exactly one, matching
    what has always been physically true.
    """

    dependencies = [
        ("openwisp_users", "0025_alter_organizationuser_is_admin"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(model_name="user", name="user_id_email_idx"),
                migrations.AddIndex(
                    model_name="user",
                    index=models.Index(
                        fields=["id", "email"], name="user_id_email_idx"
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
