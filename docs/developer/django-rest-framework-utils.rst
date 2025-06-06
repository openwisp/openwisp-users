Django REST Framework Utilities
===============================

.. include:: ../partials/developer-docs.rst

This page details the Django REST Framework classes and utilities provided
in the OpenWISP Users module. These tools support various REST API
features such as authentication, permission enforcement, multi-tenancy,
and filtering.

These utilities ensure consistency and reusability across the OpenWISP
modules.

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

Authentication
--------------

``openwisp_users.api.authentication.BearerAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``BearerAuthentication`` is the primary authentication class used in
OpenWISP's REST APIs. It is based on `TokenAuthentication
<https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication>`_
from Django REST Framework.

For detailed usage instructions, please refer to the `authenticating with
the user token :ref:`authenticating_rest_api` section.

.. _users_sesameauthentication:

``openwisp_users.api.authentication.SesameAuthentication``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``SesameAuthentication`` allows authentication using tokens generated by
`django-sesame <https://github.com/aaugustin/django-sesame>`_.

This method is primarily used for password-less authentication, such as
magic login links sent via email or SMS.

To use this authentication class, you must configure ``django-sesame``.

For more details, please see the `django-sesame documentation
<https://github.com/aaugustin/django-sesame#getting-started>`_.

Permission Classes
------------------

The custom `Django REST Framework
<https://www.django-rest-framework.org/>`_ permission classes
``IsOrganizationMember``, ``IsOrganizationManager``, and
``IsOrganizationOwner`` ensure that the requesting user belongs to the
same organization as the requested object and has the appropriate role:
member, manager, or owner, respectively.

Usage example:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics


    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationManager,)

.. _users_organization_field:

``organization_field``
~~~~~~~~~~~~~~~~~~~~~~

============ ================
**type**:    ``string``
**default**: ``organization``
============ ================

``organization_field`` specifies where to find the organization of the
current object. In most cases, this default value does not need to be
changed. However, it may need to be adjusted if the ``organization`` is
defined only on a parent object.

For example, in :doc:`openwisp-firmware-upgrader
</firmware-upgrader/index>`, the ``organization`` is defined on
``Category``, and ``Build`` has a relation to ``Category``. Therefore, the
organization of ``Build`` instances is inferred from the ``Category``
organization.

To implement the permission class correctly in such cases, you would use:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics


    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationManager,)
        organization_field = "category__organization"

This setup translates to accessing ``obj.category.organization``. Ensure
your view's querysets use `select_related
<https://docs.djangoproject.com/en/4.2/ref/models/querysets/#select-related>`_
to avoid generating too many queries.

``DjangoModelPermissions``
~~~~~~~~~~~~~~~~~~~~~~~~~~

The default ``DjangoModelPermissions`` class does not check for the
``view`` permission on objects for ``GET`` requests. The extended
``DjangoModelPermissions`` class addresses this issue. It checks for the
availability of either the ``view`` or ``change`` permissions to allow
``GET`` requests on any object.

Usage example:

.. code-block:: python

    from openwisp_users.api.permissions import DjangoModelPermissions
    from rest_framework.generics import ListCreateAPIView


    class TemplateListCreateView(ListCreateAPIView):
        serializer_class = TemplateSerializer
        permission_classes = (DjangoModelPermissions,)
        queryset = Template.objects.all()

**Note:** ``DjangoModelPermissions`` allows users who are either
organization managers or owners to view shared objects in read-only mode.

Standard users will not be able to view or list shared objects.

``ProtectedAPIMixin``
---------------------

**Full python path**: ``openwisp_users.api.mixins.ProtectedAPIMixin``.

This mixin provides a set of authentication and permission classes that
are commonly used across various OpenWISP modules API views.

Usage example:

.. code-block:: python

    # Used in openwisp-ipam
    from openwisp_users.api.mixins import (
        ProtectedAPIMixin as BaseProtectedAPIMixin,
    )


    class ProtectedAPIMixin(BaseProtectedAPIMixin):
        throttle_scope = "ipam"


    class SubnetView(ProtectedAPIMixin, RetrieveUpdateDestroyAPIView):
        serializer_class = SubnetSerializer
        queryset = Subnet.objects.all()

Mixins for Multi-Tenancy
------------------------

Filtering Items by Organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The custom `Django REST Framework
<https://www.django-rest-framework.org/>`_ mixins
``FilterByOrganizationMembership``, ``FilterByOrganizationManaged`` and
``FilterByOrganizationOwned`` can be used in the API views to ensure that
the current user is able to see only the data related to their
organization when accessing the API view.

These classes work by filtering the queryset so that only items related to
organizations the user is member, manager or owner of, respectively.

These mixins ship the Django REST Framework's `IsAuthenticated
<https://www.django-rest-framework.org/api-guide/permissions/#isauthenticated>`_
permission class by default because the organization filtering works only
on authenticated users. Always remember to include this class when
overriding ``permission_classes`` in a view.

Usage example:

.. code-block:: python

    from openwisp_users.api.mixins import FilterByOrganizationManaged
    from rest_framework import generics


    class UsersListView(FilterByOrganizationManaged, generics.ListAPIView):
        """
        UsersListView will show only users from organizations managed
        by current user in the list.
        """

        pass


    class ExampleListView(FilterByOrganizationManaged, generics.ListAPIView):
        """
        Example showing how to extend ``permission_classes``.
        """

        permission_classes = FilterByOrganizationManaged.permission_classes + [
            # additional permission classes here
        ]

Checking Parent Objects
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, the API view needs to check the existence and the
``organization`` field of a parent object.

In such cases, ``FilterByParentMembership``, ``FilterByParentManaged`` and
``FilterByParentOwned`` can be used.

For example, given a hypothetical URL
``/api/v1/device/{device_id}/config/``, the view must check that
``{device_id}`` exists and that the user has access to it, here's how to
do it:

.. code-block:: python

    import swapper
    from rest_framework import generics
    from openwisp_users.api.mixins import FilterByParentManaged

    Device = swapper.load_model("config", "Device")
    Config = swapper.load_model("config", "Config")

    # URL is:
    # /api/v1/device/{device_id}/config/


    class ConfigListView(FilterByParentManaged, generics.DetailAPIView):
        model = Config

        def get_parent_queryset(self):
            qs = Device.objects.filter(pk=self.kwargs["device_id"])
            return qs

Multi-tenant Serializers for the Browsable Web UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Django REST Framework <https://www.django-rest-framework.org/>`_ provides
a browsable API which can be used to create HTTP requests right from the
browser.

The relationship fields in this interface show all the relationships,
without filtering by the organization the user has access to, which breaks
multi-tenancy.

The ``FilterSerializerByOrgMembership``, ``FilterSerializerByOrgManaged``
and ``FilterSerializerByOrgOwned`` can be used to solve this issue.

These serializers do not allow non-superusers to create shared objects.

Usage example:

.. code-block:: python

    from openwisp_users.api.mixins import FilterSerializerByOrgOwned
    from rest_framework.serializers import ModelSerializer
    from .models import Device


    class DeviceSerializer(FilterSerializerByOrgOwned, ModelSerializer):
        class Meta:
            model = Device
            fields = "__all__"

The ``include_shared`` boolean attribute can be used to include shared
objects in the accepted values of the multi-tenant serializers.

Shared objects have the ``organization`` field set to ``None`` and can be
used by any organization. A common use case is :ref:`shared templates in
OpenWISP Controller <controller_shared_vs_org>`.

Usage example:

.. code-block:: python

    from openwisp_users.api.mixins import FilterSerializerByOrgOwned
    from rest_framework.serializers import ModelSerializer
    from .models import Book


    class BookSerializer(FilterSerializerByOrgOwned, ModelSerializer):
        include_shared = True

        class Meta:
            model = Book
            fields = "__all__"

To filter items based on the ``organization`` of their parent object,
``organization_field`` attribute can be defined in the view function which
is inheriting any of the mixin classes.

Usage example: :ref:`organization_field <users_organization_field>`.

Multi-tenant Filtering Capabilities for the Browsable Web UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration of `Django filters
<https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html>`_
with `Django REST Framework <https://www.django-rest-framework.org/>`_ is
provided through a DRF-specific ``FilterSet`` and a ``filter backend``.

The relationship fields of ``django-filters`` show all the available
results, without filtering by the organization the user has access to,
which breaks multi-tenancy.

The ``FilterDjangoByOrgMembership``, ``FilterDjangoByOrgManaged`` and
``FilterDjangoByOrgOwned`` can be used to solve this issue.

Usage example:

.. code-block:: python

    from django_filters import rest_framework as filters
    from openwisp_users.api.mixins import FilterDjangoByOrgManaged
    from ..models import FloorPlan


    class FloorPlanOrganizationFilter(FilterDjangoByOrgManaged):
        organization_slug = filters.CharFilter(field_name="organization__slug")

        class Meta:
            model = FloorPlan
            fields = ["organization", "organization_slug"]


    class FloorPlanListCreateView(ProtectedAPIMixin, generics.ListCreateAPIView):
        serializer_class = FloorPlanSerializer
        queryset = FloorPlan.objects.select_related().order_by("-created")
        pagination_class = ListViewPagination
        filter_backends = [filters.DjangoFilterBackend]
        filterset_class = FloorPlanOrganizationFilter

You can also use the organization filter classes such as
``OrganizationManagedFilter`` from ``openwisp_users.api.filters`` which
includes ``organization`` and ``organization_slug`` filter fields by
default.

Usage example:

.. code-block:: python

    from django_filters import rest_framework as filters
    from openwisp_users.api.filters import OrganizationManagedFilter
    from ..models import FloorPlan


    class FloorPlanFilter(OrganizationManagedFilter):
        class Meta(OrganizationManagedFilter.Meta):
            model = FloorPlan


    class FloorPlanListCreateView(ProtectedAPIMixin, generics.ListCreateAPIView):
        serializer_class = FloorPlanSerializer
        queryset = FloorPlan.objects.select_related().order_by("-created")
        pagination_class = ListViewPagination
        filter_backends = [filters.DjangoFilterBackend]
        filterset_class = FloorPlanFilter
