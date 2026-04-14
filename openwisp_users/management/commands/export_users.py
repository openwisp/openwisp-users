import csv

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from ... import settings as app_settings

User = get_user_model()


def normalize_field(field):
    """Normalize a string or dict field definition to a dict."""
    if isinstance(field, dict):
        return field
    return {"name": field}


class Command(BaseCommand):
    help = _("Exports user data to a CSV file")

    def _normalize_value(self, value):
        """Convert None to empty string, otherwise stringify the value."""
        return "" if value is None else str(value)

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-fields",
            dest="exclude_fields",
            default="",
            help=_("Comma-separated list of fields to exclude from export"),
        )
        parser.add_argument(
            "--filename",
            dest="filename",
            default="openwisp_exported_users.csv",
            help=_(
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
        with open(filename, "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            # Write header row using the name of each field
            csv_writer.writerow([normalize_field(f)["name"] for f in fields])

            # Write data rows
            for user in queryset.iterator(chunk_size=1000):
                row = []
                for field in fields:
                    val = self._get_field_value(user, field)
                    row.append(val)
                csv_writer.writerow(row)
        self.stdout.write(
            self.style.SUCCESS(
                _("User data exported successfully to {filename}!").format(
                    filename=filename
                )
            )
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
            # convert None -> empty string to avoid 'None' literals in CSV
            row = []
            for f in subfields:
                val = self._get_nested_attr(obj, f)
                row.append(self._normalize_value(val))
            rows.append(row)
        if not rows:
            return ""
        if len(subfields) == 1:
            return ",".join(row[0] for row in rows)
        return "(" + ",".join("(" + ",".join(row) + ")" for row in rows) + ")"

    def _get_nested_attr(self, obj, attr_path):
        """Resolve a dotted attribute path on an object.

        Returns the resolved value or None when an intermediate attribute
        is missing or raises ObjectDoesNotExist/AttributeError. When a
        related manager/queryset is encountered (detected via QuerySet
        instance or presence of `all()`), the remaining path is resolved
        for each item and results are combined.
        """
        if not attr_path:
            return obj
        parts = attr_path.split(".")
        current = obj
        for i, part in enumerate(parts):
            try:
                current = getattr(current, part)
            except (ObjectDoesNotExist, AttributeError):
                # missing attribute or intermediate raises -> None sentinel
                return None
            # Detect querysets/related managers robustly.
            if (isinstance(current, (QuerySet, BaseManager))) and (i < len(parts) - 1):
                remaining_path = ".".join(parts[i + 1 :])
                # We use current.all() instead of current.iterator() to utilize
                # the prefetch_related queryset cache. The iterator() method
                # would bypass the cache and cause additional queries.
                values = []
                for item in current.all():
                    v = self._get_nested_attr(item, remaining_path)
                    values.append(self._normalize_value(v))
                return ",".join(values)
        return current

    def _get_field_value(self, user, field):
        normalized = normalize_field(field)
        name = normalized["name"]
        callable_fn = normalized.get("callable")
        subfields = normalized.get("fields")
        # Priority: callable > fields > name
        if callable_fn is not None:
            try:
                val = callable_fn(user)
            except Exception as e:
                func_name = getattr(callable_fn, "__name__", repr(callable_fn))
                raise CommandError(
                    _(
                        "Error calling function {func_name!r} for field '{name}': {e}"
                    ).format(func_name=func_name, name=name, e=e)
                )
            return self._normalize_value(val)
        if subfields is not None:
            attr = self._get_nested_attr(user, name)
            if attr is None:
                return ""
            if isinstance(attr, (QuerySet, BaseManager)):
                return self.serialize_related(attr, subfields)
            return ",".join(
                self._normalize_value(self._get_nested_attr(attr, f)) for f in subfields
            )
        val = self._get_nested_attr(user, name)
        if isinstance(val, (QuerySet, BaseManager)):
            return ""
        return self._normalize_value(val)
