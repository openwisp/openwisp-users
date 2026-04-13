import csv

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from ... import settings as app_settings

User = get_user_model()


def normalize_field(field):
    """Normalize a string or dict field definition to a dict."""
    if isinstance(field, dict):
        return field
    return {"name": field}


def serialize_related(manager, subfields):
    """Serialize a RelatedManager queryset using the given subfields.

    Single subfield → comma-separated values: val1,val2,...
    Multiple subfields → tuple-per-row format: ((v1,v2),(v3,v4))
    """
    rows = [[str(getattr(obj, f, "")) for f in subfields] for obj in manager.all()]
    if not rows:
        return ""
    if len(subfields) == 1:
        return ",".join(row[0] for row in rows)
    return "(" + ",".join("(" + ",".join(row) + ")" for row in rows) + ")"


class Command(BaseCommand):
    help = "Exports user data to a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-fields",
            dest="exclude_fields",
            default="",
            help="Comma-separated list of fields to exclude from export",
        )
        parser.add_argument(
            "--filename",
            dest="filename",
            default="openwisp_exported_users.csv",
            help=(
                "Filename for the exported CSV, defaults to"
                ' "openwisp_exported_users.csv"'
            ),
        )

    def handle(self, *args, **options):
        fields = app_settings.EXPORT_USERS_COMMAND_CONFIG.get("fields", []).copy()
        # Get the fields to be excluded from the command-line argument
        exclude_fields = options.get("exclude_fields").split(",")
        # Remove excluded fields from the export fields (match on the field name)
        fields = [
            field
            for field in fields
            if normalize_field(field)["name"] not in exclude_fields
        ]
        # Fetch all user data using select_related and prefetch_related
        queryset = (
            User.objects.select_related(
                *app_settings.EXPORT_USERS_COMMAND_CONFIG.get("select_related", []),
            )
            .prefetch_related(
                *app_settings.EXPORT_USERS_COMMAND_CONFIG.get("prefetch_related", []),
            )
            .order_by("date_joined")
        )

        # Prepare a CSV writer
        filename = options.get("filename")
        with open(filename, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            # Write header row using the name of each field
            csv_writer.writerow([normalize_field(f)["name"] for f in fields])

            # Write data rows
            for user in queryset.iterator(chunk_size=1000):
                csv_writer.writerow(
                    [self._get_field_value(user, field) for field in fields]
                )
        self.stdout.write(
            self.style.SUCCESS(f"User data exported successfully to {filename}!")
        )

    def _get_field_value(self, user, field):
        normalized = normalize_field(field)
        name = normalized["name"]
        callable_fn = normalized.get("callable")
        subfields = normalized.get("fields")
        # Priority: callable > fields > name
        if callable_fn is not None:
            try:
                return callable_fn(user)
            except Exception as e:
                raise Exception(f"Error calling function for field '{name}': {e}")
        if subfields is not None:
            try:
                attr = getattr(user, name)
            except ObjectDoesNotExist:
                return ""
            if attr is None:
                return ""
            if hasattr(attr, "iterator"):
                return serialize_related(attr, subfields)
            return ",".join(str(getattr(attr, f, "")) for f in subfields)

        # Dot-notation: e.g. "auth_token.key" or "profile.phone_number"
        if "." in name:
            model_attr, sub_attr = name.split(".", 1)
            try:
                intermediate = getattr(user, model_attr)
            except ObjectDoesNotExist:
                return ""
            if hasattr(intermediate, "iterator"):
                # Related manager accessed via dot notation → comma-separated values
                return ",".join(
                    str(getattr(obj, sub_attr, "")) for obj in intermediate.iterator()
                )
            try:
                return getattr(intermediate, sub_attr)
            except ObjectDoesNotExist:
                return ""
        return getattr(user, name)
