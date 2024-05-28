Organization membership helpers
-------------------------------

.. include:: ../partials/developer-docs.rst

The ``User`` model provides methods to check whether the user
is a member, manager or owner of an organization in an efficient way.

These methods are needed because an user may be administrator in one organization,
but simple end-user is another organization, so we need to easily distinguish
between the different use cases and at the same time avoid to generate too
many database queries.

.. code-block:: python

    import swapper

    User = swapper.load_model('openwisp_users', 'User')
    Organization = swapper.load_model('openwisp_users', 'Organization')

    user = User.objects.first()
    org = Organization.objects.first()
    user.is_member(org)
    user.is_manager(org)
    user.is_owner(org)

    # also valid (avoids query to retrieve Organization instance)
    device = Device.objects.first()
    user.is_member(device.organization_id)
    user.is_manager(device.organization_id)
    user.is_owner(device.organization_id)

``is_member(org)``
~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance passed.
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

This check shall be used when access needs to be granted to end-users who
need to consume a service offered by an organization they're member of
(eg: authenticate to a public wifi service).

``is_manager(org)``
~~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance
and has the ``OrganizationUser.is_admin`` field set to ``True``.
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

This check shall be used when access needs to be granted to the managers of
an organization users who need to perform administrative tasks,
eg: create, edit or delete objects of their organization,
access or download sensitive information like firmware images,
edit users of their organization, etc.

``is_owner(org)``
~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance
and is owner of the organization (checks the presence of an
``OrganizationOwner`` instance for the user).
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

There can be only one owner for each organization.

This check shall be used to avoid that managers would be able to take control
of an organization and exclude the original owner without their consent.

``organizations_dict``
~~~~~~~~~~~~~~~~~~~~~~

The methods described above use the ``organizations_dict`` property method under
the hood, which builds a dictionary in which each key contains the primary key
of the organization the user is member of, and each key contains another dictionary
which allows to easily determine if the user is manager (``is_admin``) and owner
(``is_owner``).

**This data structure is cached automatically and accessing it multiple times
over the span of multiple requests will not generate multiple database queries.**

The cache invalidation also happens automatically whenever an ``OrganizationUser``
or an ``OrganizationOwner`` instance is added, changed or deleted.

Usage exmaple:

.. code-block:: python

    >>> user.organizations_dict
    ... {'20135c30-d486-4d68-993f-322b8acb51c4': {'is_admin': True, 'is_owner': False}}
    >>> user.organizations_dict.keys()
    ... dict_keys(['20135c30-d486-4d68-993f-322b8acb51c4'])

``organizations_managed``
~~~~~~~~~~~~~~~~~~~~~~~~~

This attribute returns a list containing the primary keys of the organizations
which the user can manage.

Usage example:

.. code-block:: python

    >>> user.organizations_managed
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

``organizations_owned``
~~~~~~~~~~~~~~~~~~~~~~~

This attribute returns a list containing the primary keys of the organizations
which the user owns.

Usage example:

.. code-block:: python

    >>> user.organizations_owned
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']
