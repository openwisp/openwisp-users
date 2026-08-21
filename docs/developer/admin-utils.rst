Admin Utilities
===============

This section outlines the admin utilities provided by the OpenWISP Users
module.

.. contents:: **Table of contents**:
    :depth: 2
    :local:

``MultitenantAdminMixin``
-------------------------

**Full python path**:
``openwisp_users.multitenancy.MultitenantAdminMixin``.

Adding this mixin to a ``ModelAdmin`` class makes it multitenant-capable,
allowing users to see only items of the organizations they manage or own.

This class has two important attributes:

- ``multitenant_shared_relations``: If the model has relations (e.g.,
  ``ForeignKey``, ``OneToOne``) to other multitenant models with an
  ``organization`` field, list those model attributes here as a list of
  strings. See `how it is used in OpenWISP Controller
  <https://github.com/openwisp/openwisp-controller/search?q=multitenant_shared_relations>`_
  for a real-world example.
- ``multitenant_parent``: If the admin model relies on a parent model with
  the ``organization`` field, specify the field pointing to the parent
  here. See `how it is used in OpenWISP Firmware Upgrader
  <https://github.com/openwisp/openwisp-firmware-upgrader/search?q=multitenant_parent>`_
  for a real-world example.

Disabled Organization Write Protection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``MultitenantAdminMixin`` also blocks changes to any object belonging to a
:ref:`disabled organization <users_disabled_organization>`, while still
allowing it to be viewed and deleted. This also applies to superusers. For
models whose organization is reached through a parent, the mixin follows
``multitenant_parent`` to protect those objects too.

This is controlled by the ``disabled_organization_write_protection`` class
attribute, which defaults to ``True``. Set it to ``False`` on a specific
``ModelAdmin`` to opt out:

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.multitenancy import MultitenantAdminMixin


    class BookAdmin(MultitenantAdminMixin, admin.ModelAdmin):
        disabled_organization_write_protection = False
        # other attributes

The ``organization`` form field excludes disabled organizations for
everyone, including superusers. An opted-out admin keeps the object's
current disabled organization selectable so it can be saved.

The same protection applies to **inlines** attached to a disabled object.
The parent admin denies adding and changing inline rows but keeps deletion
available, even when an inline does not use the mixin. Set
``disabled_organization_write_protection = False`` on the parent admin or
on an individual inline to opt out.

Custom admin actions are also blocked for disabled-organization objects,
except for deletion actions. To allow a specific lifecycle action while
keeping the rest of the protection enabled, list its name in
``disabled_organization_action_exclusions``:

.. code-block:: python

    class DeviceAdmin(MultitenantAdminMixin, admin.ModelAdmin):
        disabled_organization_action_exclusions = ("deactivate_device",)

The mixin resolves an object's organization from ``organization`` by
default and follows ``multitenant_parent`` when configured. Admins using
another relation can override ``get_object_organization()`` to return the
related organization.

``MultitenantOrgFilter``
------------------------

**Full python path**:
``openwisp_users.multitenancy.MultitenantOrgFilter``.

This auto complete admin filter displays only organizations the current
user can manage. Below is an example of adding the auto complete
organization filter in ``BookAdmin``:

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.multitenancy import MultitenantOrgFilter


    class BookAdmin(admin.ModelAdmin):
        list_filter = [
            MultitenantOrgFilter,
        ]
        # other attributes

``MultitenantRelatedOrgFilter``
-------------------------------

**Full python path**:
``openwisp_users.multitenancy.MultitenantRelatedOrgFilter``.

This filter is similar to ``MultitenantOrgFilter`` but displays only
objects related to organizations the current user can manage. Use this for
creating filters for related multitenant models.

Consider the following example from `IpAddressAdmin in openwisp-ipam
<https://github.com/openwisp/openwisp-ipam/blob/956d9d25fc1ac339cb148ec7faf80046cc14be37/openwisp_ipam/admin.py#L216-L227>`_.
``IpAddressAdmin`` allows filtering ``IpAddress`` objects by ``Subnet``
belonging to organizations managed by the user.

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.multitenancy import MultitenantRelatedOrgFilter
    from swapper import load_model

    Subnet = load_model("openwisp_ipam", "Subnet")


    class SubnetFilter(MultitenantRelatedOrgFilter):
        field_name = "subnet"
        parameter_name = "subnet_id"
        title = _("subnet")


    @admin.register(IpAddress)
    class IpAddressAdmin(
        VersionAdmin,
        MultitenantAdminMixin,
        TimeReadonlyAdminMixin,
        ModelAdmin,
    ):
        list_filter = [SubnetFilter]
        # other options
