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

``MultitenantAdminMixin`` protects objects belonging to a :ref:`disabled
organization <users_disabled_organization>`, including objects linked
through ``multitenant_parent``:

- Superusers can view and delete the objects, but cannot change them.
  Non-superusers cannot access objects in disabled organizations through
  this mixin, even if they have the model's view or delete permission.
- Organization and related-object choices exclude disabled organizations.
- The organization admin allows superusers to re-enable the organization.

Inlines
+++++++

When the parent belongs to a disabled organization, the mixin prevents
adding or editing its inline rows, even if the inline does not use the
mixin. Deleting an inline row through the form requires permission to
change the parent.

An editable parent, such as a user, can also have individual inline rows
belonging to disabled organizations. Use
``MultitenantReadOnlyInlineFormSet`` to make those rows read-only while
still allowing deletion.

Admin Actions
+++++++++++++

Actions are blocked if any selected object belongs to a disabled
organization. The built-in ``delete_selected`` and
``delete_selected_overridden`` actions are excluded by default. To allow
another cleanup action, list its name in
``disabled_organization_action_exclusions``:

.. code-block:: python

    class DeviceAdmin(MultitenantAdminMixin, admin.ModelAdmin):
        disabled_organization_action_exclusions = ("deactivate_device",)

Customization
+++++++++++++

For a cleanup operation that needs to bypass write protection, set
``disabled_organization_write_protection = False`` on its ``ModelAdmin``
or inline. The default is ``True``:

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.multitenancy import MultitenantAdminMixin


    class BookAdmin(MultitenantAdminMixin, admin.ModelAdmin):
        disabled_organization_write_protection = False
        # other attributes

An opted-out admin keeps the object's current disabled organization
selectable so it can be saved. The opt-out does not disable field
protection provided by ``MultitenantReadOnlyInlineFormSet``.

If an object uses a different relationship to its organization, override
``get_object_organization()`` on its admin to return the organization.

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
