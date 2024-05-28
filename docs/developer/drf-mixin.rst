Django REST Framework Mixins
----------------------------

.. include:: ../partials/developer-docs.rst

Filtering items by organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The custom `Django REST Framework <https://www.django-rest-framework.org/>`_
mixins ``FilterByOrganizationMembership``, ``FilterByOrganizationManaged``
and ``FilterByOrganizationOwned`` can be used in the API views to ensure
that the current user is able to see only the data related to their
organization when accessing the API view.

They work by filtering the queryset so that only items related
to organizations the user is member, manager or owner of, respectively.

These mixins ship the Django REST Framework's
`IsAuthenticated
<https://www.django-rest-framework.org/api-guide/permissions/#isauthenticated>`_
permission class by default because the organization filtering
works only on authenticated users.
Always remember to include this class when
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

Checking parent objects
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, the API view needs to check the existence and the
``organization`` field of a parent object.

In such cases, ``FilterByParentMembership``,
``FilterByParentManaged`` and ``FilterByParentOwned`` can be used.

For example, given a hypotetical URL ``/api/v1/device/{device_id}/config/``,
the view must check that ``{device_id}`` exists and that the user
has access to it, here's how to do it:

.. code-block:: python

    import swapper
    from rest_framework import generics
    from openwisp_users.api.mixins import FilterByParentManaged

    Device = swapper.load_model('config', 'Device')
    Config = swapper.load_model('config', 'Config')

    # URL is:
    # /api/v1/device/{device_id}/config/

    class ConfigListView(FilterByParentManaged, generics.DetailAPIView):
        model = Config

        def get_parent_queryset(self):
            qs = Device.objects.filter(pk=self.kwargs['device_id'])
            return qs

Multi-tenant serializers for the browsable web UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Django REST Framework <https://www.django-rest-framework.org/>`_
provides a browsable API which can be used to create HTTP requests right
from the browser.

The relationship fields in this interface show all the relationships,
without filtering by the organization the user has access to, which
breaks multi-tenancy.

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
            fields = '__all__'

The ``include_shared`` boolean attribute can be used to include shared
objects in the accepted values of the multi-tenant serializers.

Shared objects have the ``organization`` field set to ``None`` and can
be used by any organization. A common use case is `shared templates
in OpenWISP Controller
<https://openwisp.io/docs/user/templates.html#shared-templates-vs-organization-specific>`_.

Usage example:

.. code-block:: python

    from openwisp_users.api.mixins import FilterSerializerByOrgOwned
    from rest_framework.serializers import ModelSerializer
    from .models import Book

    class BookSerializer(FilterSerializerByOrgOwned, ModelSerializer):
        include_shared = True

        class Meta:
            model = Book
            fields = '__all__'

To filter items based on the ``organization`` of their parent object,
``organization_field`` attribute can be defined in the view function
which is inheriting any of the mixin classes.

Usage example: `organization_field
<https://github.com/openwisp/openwisp-users#organization_field>`_.

Multi-tenant filters capabilities for the browsable web UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration of `Django filters <https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html>`_
with `Django REST Framework <https://www.django-rest-framework.org/>`_
is provided through a DRF-specific ``FilterSet`` and a ``filter backend``.

The relationship fields of ``django-filters`` show all the available results,
without filtering by the organization the user has access to,
which breaks multi-tenancy.

The ``FilterDjangoByOrgMembership``, ``FilterDjangoByOrgManaged``
and ``FilterDjangoByOrgOwned`` can be used to solve this issue.

Usage example:

.. code-block:: python

   from django_filters import rest_framework as filters
   from openwisp_users.api.mixins import FilterDjangoByOrgManaged
   from ..models import FloorPlan


   class FloorPlanOrganizationFilter(FilterDjangoByOrgManaged):
       organization_slug = filters.CharFilter(field_name='organization__slug')

       class Meta:
           model = FloorPlan
           fields = ['organization', 'organization_slug']


   class FloorPlanListCreateView(ProtectedAPIMixin, generics.ListCreateAPIView):
       serializer_class = FloorPlanSerializer
       queryset = FloorPlan.objects.select_related().order_by('-created')
       pagination_class = ListViewPagination
       filter_backends = [filters.DjangoFilterBackend]
       filterset_class = FloorPlanOrganizationFilter

You can also use the organization filter classes
such as ``OrganizationManagedFilter`` from ``openwisp_users.api.filters``
which includes ``organization`` and ``organization_slug`` filter fields by default.

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
       queryset = FloorPlan.objects.select_related().order_by('-created')
       pagination_class = ListViewPagination
       filter_backends = [filters.DjangoFilterBackend]
       filterset_class = FloorPlanFilter
