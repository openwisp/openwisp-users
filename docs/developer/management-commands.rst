Management Commands
-------------------

.. include:: /partials/developers-docs-warning.rst

.. _export_users:

``export_users``
~~~~~~~~~~~~~~~~

This command exports user data to a CSV file, including related data such as organizations.

**Arguments**:

- `--exclude-fields`: Optional, comma-separated list of fields to exclude from the export.
- `--filename`: Optional, filename for the exported CSV, defaults to "openwisp_exported_users.csv".

Example usage:

.. code-block:: shell

    ./manage.py export_users --exclude-fields birth_date,location --filename users.csv

For advance customizations (e.g. adding fields for export), you can use the
:ref:`OPENWISP_USERS_EXPORT_USERS_COMMAND_CONFIG <openwisp_users_export_users_command_config>`_
setting.

ProtectedAPIMixin
~~~~~~~~~~~~~~~~~

This mixin provides a set of authentication and permission classes
that are used across various OpenWISP modules API views.

Usage example:

.. code-block:: python

    # Used in openwisp-ipam
    from openwisp_users.api.mixins import ProtectedAPIMixin as BaseProtectedAPIMixin

    class ProtectedAPIMixin(BaseProtectedAPIMixin):
        throttle_scope = 'ipam'

    class SubnetView(ProtectedAPIMixin, RetrieveUpdateDestroyAPIView):
        serializer_class = SubnetSerializer
        queryset = Subnet.objects.all()
