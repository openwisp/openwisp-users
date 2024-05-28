Django REST Framework Permission Classes
========================================

.. include:: ../partials/developer-docs.rst

The custom `Django REST Framework <https://www.django-rest-framework.org/>`_ permission
classes ``IsOrganizationMember``, ``IsOrganizationManager`` and ``IsOrganizationOwner``
can be used in the API to ensure that the request user is in the same organization as
requested object and is organization member, manager or owner respectively. Usage
example:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics


    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationManager,)

``organization_field``
----------------------

============ ================
**type**:    ``string``
**default**: ``organization``
============ ================

``organization_field`` can be used to define where to look to find the organization of
the current object. In most cases this won't need to be changed, but it does need to be
changed when the ``organization`` is defined only on a parent object.

For example, in `openwisp-firmware-upgrader
<https://github.com/openwisp/openwisp-firmware-upgrader>`_, ``organization`` is defined
on ``Category`` and ``Build`` has a relation to ``category``, so the organization of
Build instances is inferred from the organization of the Category.

Therefore, to implement the permission class correctly, we would have to do:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics


    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationManager,)
        organization_field = "category__organization"

This will translate into accessing ``obj.category.organization``. Ensure the queryset of
your views make use of `select_related
<https://docs.djangoproject.com/en/3.0/ref/models/querysets/#select-related>`_ in these
cases to avoid generating too many queries.

``DjangoModelPermissions``
--------------------------

The default ``DjangoModelPermissions`` class doesn't checks for the ``view`` permission
of any object for ``GET`` requests. The extended ``DjangoModelPermissions`` class
overcomes this problem. In order to allow ``GET`` requests on any object it checks for
the availability of either ``view`` or ``change`` permissions.

Usage example:

.. code-block:: python

    from openwisp_users.api.permissions import DjangoModelPermissions
    from rest_framework.generics import ListCreateAPIView


    class TemplateListCreateView(ListCreateAPIView):
        serializer_class = TemplateSerializer
        permission_classes = (DjangoModelPermissions,)
        queryset = Template.objects.all()

**Note:** ``DjangoModelPermissions`` allows users who are either organization managers
or owners to view shared objects in read only mode.

Standard users will not be able to view or list shared objects.
