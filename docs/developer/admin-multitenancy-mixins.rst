Admin Multitenancy mixins
=========================

.. include:: ../partials/developer-docs.rst

- **MultitenantAdminMixin**: adding this mixin to a ``ModelAdmin`` class will make it
  multitenant-capable (users will only be able to see items of the organizations they
  manage or own).

  This class has two important attributes that can be set:

  - ``multitenant_shared_relations``: if the model has relations (eg: ``ForeignKey``,
    ``OneToOne``) to other models which are also multitenant (that is, they have an
    ``organization`` field), you want the admin to only show the relations the user can
    manage, the way to do that is to list those model attributes here as a list of
    strings. See `how it is used in OpenWISP Controller
    <https://github.com/openwisp/openwisp-controller/search?q=multitenant_shared_relations>`_
    for a real world example.
  - ``multitenant_parent``: if the admin model does not have an ``organization`` field,
    but instead relies on a parent model which has the field, then you can specify here
    the field which points to the parent. See `how it is used in OpenWISP Firmware
    Upgrader
    <https://github.com/openwisp/openwisp-firmware-upgrader/search?q=multitenant_parent>`_
    for a real world example.

- **MultitenantOrgFilter**: an autocomplete admin filter that shows only organizations
  the current user can manage in its available choices. The following example adds the
  autocomplete organization filter in ``BookAdmin``:

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.multitenancy import MultitenantOrgFilter


    class BookAdmin(admin.ModelAdmin):
        list_filter = [
            MultitenantOrgFilter,
        ]
        # other attributes

- **MultitenantRelatedOrgFilter**: similar ``MultitenantOrgFilter`` but shows only
  objects which have a relation with one of the organizations the current user can
  manage, this shall be used for creating filters for related multitenant models.

  Consider the following example of `IpAddressAdmin from openwisp-ipam
  <https://github.com/openwisp/openwisp-ipam/blob/956d9d25fc1ac339cb148ec7faf80046cc14be37/openwisp_ipam/admin.py#L216-L227>`_
  . ``IpAddressAdmin`` allows filtering `IpAddress
  <https://github.com/openwisp/openwisp-ipam/blob/956d9d25fc1ac339cb148ec7faf80046cc14be37/openwisp_ipam/base/models.py#L276-L281>`_
  objects by ``Subnet`` that belongs to organizations managed by the user.

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
        VersionAdmin, MultitenantAdminMixin, TimeReadonlyAdminMixin, ModelAdmin
    ):
        list_filter = [SubnetFilter]
        # other options
