Management Commands
===================

.. _export_users:

``export_users``
----------------

This command exports user data to a CSV file, including related data such
as organizations.

**Arguments**:

- ``--exclude-fields``: Optional, comma-separated list of fields to
  exclude from the export.
- ``--filename``: Optional, filename for the exported CSV, defaults to
  "openwisp_exported_users.csv".

Example usage:

.. code-block:: shell

    ./manage.py export_users --exclude-fields birth_date,location --filename users.csv

For advanced customizations (e.g., adding fields for export), you can use
the :ref:`OPENWISP_USERS_EXPORT_USERS_COMMAND_CONFIG` setting.
