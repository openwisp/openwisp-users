import random
from time import sleep

from django.conf import settings

if "reversion" in settings.INSTALLED_APPS:  # pragma: no cover
    from reversion.admin import VersionAdmin as BaseModelAdmin
else:
    from django.contrib.admin import ModelAdmin as BaseModelAdmin


class BaseAdmin(BaseModelAdmin):
    history_latest_first = True


def usermodel_add_form(model, additional_fields):
    """
    Read:
    https://github.com/openwisp/openwisp-users/blob/master/README.rst#usermodel_add_form
    """

    for field in additional_fields:
        modelMeta = model.add_form.Meta
        # Add form fieldsets
        add_fieldsets = modelMeta.fieldsets[0][1]["fields"][:]
        modelMeta.fieldsets[0][1]["fields"] = (
            add_fieldsets[: field[0]] + [field[1]] + add_fieldsets[field[0] :]
        )
        # Add form fieldsets_superuser
        add_fieldsets_superuser = modelMeta.fieldsets_superuser[0][1]["fields"][:]
        modelMeta.fieldsets_superuser[0][1]["fields"] = (
            add_fieldsets_superuser[: field[0]]
            + [field[1]]
            + add_fieldsets_superuser[field[0] :]
        )


def usermodel_change_form(model, additional_fields):
    """
    Read:
    https://github.com/openwisp/openwisp-users/blob/master/README.rst#usermodel_change_form
    """

    # Change form fieldsets
    for field in additional_fields:
        for fieldset in model.fieldsets:
            fieldsets = list(fieldset[1].get("fields", ()))
            if "first_name" not in fieldsets:
                continue
            fieldset[1]["fields"] = (
                fieldsets[: field[0]] + [field[1]] + fieldsets[field[0] :]
            )
            break


def usermodel_list_and_search(model, additional_fields):
    """
    Read:
    https://github.com/openwisp/openwisp-users/blob/master/README.rst#usermodel_list_and_search
    """

    # Change form fieldsets
    for field in additional_fields:
        displays = model.list_display[:]
        model.list_display = displays[: field[0]] + [field[1]] + displays[field[0] :]
        model.search_fields += (field[1],)


def throttle_email_batch(email_count):
    """
    Throttle email batch processing by sleeping every 10th email.

    Args:
        email_count: Current count of emails sent in the batch
    """
    if email_count and email_count % 10 == 0:
        sleep(random.randint(1, 2))
