import csv

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from ... import settings as app_settings

User = get_user_model()


def normalize_field(field):
    """Normalize a string or dict field definition to a dict."""
    if isinstance(field, dict):
        return field
    return {"name": field}


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
        raw_fields = app_settings.EXPORT_USERS_COMMAND_CONFIG.get("fields", []).copy()
        # Get the fields to be excluded from the command-line argument
        exclude_fields = [
            t.strip() for t in options.get("exclude_fields").split(",") if t.strip()
        ]
        # Remove excluded fields from the export fields (match on the field name)
        fields = [
            field
            for field in raw_fields
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

    def serialize_related(self, manager, subfields):
        """Serialize a RelatedManager queryset using the given subfields.

        Single subfield → comma-separated values: val1,val2,...
        Multiple subfields → tuple-per-row format: ((v1,v2),(v3,v4))
        """
        rows = []
        # We use manager.all() instead of manager.iterator() to utilize the
        # prefetch_related queryset cache. The iterator() method would bypass the cache
        # and cause additional queries.
        for obj in manager.all():
            rows.append([str(self._get_nested_attr(obj, f)) for f in subfields])
        if not rows:
            return ""
        if len(subfields) == 1:
            return ",".join(row[0] for row in rows)
        return "(" + ",".join("(" + ",".join(row) + ")" for row in rows) + ")"

    def _get_nested_attr(self, obj, attr_path):
        if not attr_path:
            return obj
        parts = attr_path.split(".")
        current = obj
        for i, part in enumerate(parts):
            try:
                current = getattr(current, part)
            except (ObjectDoesNotExist, AttributeError):
                return ""
            if hasattr(current, "iterator") and i < len(parts) - 1:
                remaining_path = ".".join(parts[i + 1 :])
                # We use current.all() instead of current.iterator() to utilize
                # the prefetch_related queryset cache. The iterator() method
                # would bypass the cache and cause additional queries.
                return ",".join(
                    str(self._get_nested_attr(item, remaining_path))
                    for item in current.all()
                )
        return current

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
                raise CommandError(f"Error calling function for field '{name}': {e}")
        if subfields is not None:
            attr = self._get_nested_attr(user, name)
            if attr is None:
                return ""
            if hasattr(attr, "iterator"):
                return self.serialize_related(attr, subfields)
            return ",".join(str(self._get_nested_attr(attr, f)) for f in subfields)
        return self._get_nested_attr(user, name)
