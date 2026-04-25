Settings
========

.. include:: /partials/settings-note.rst

``OPENWISP_ORGANIZATION_USER_ADMIN``
------------------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the admin section for managing ``OrganizationUser``
items is enabled or not.

``OPENWISP_ORGANIZATION_OWNER_ADMIN``
-------------------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the admin section for managing ``OrganizationOwner``
items is enabled or not.

Refer to :ref:`organization_owners` for more information.

``OPENWISP_USERS_SOCIALACCOUNT_ADMIN_NEEDED``
---------------------------------------------

============ =========================================
**type**:    ``boolean``
**default**: auto-detected based on ``INSTALLED_APPS``
============ =========================================

Controls whether the social account admin (used to manage OAuth/SAML
application credentials such as client IDs and secrets) is shown in the
Django admin.

By default, this is set to ``True`` automatically when any app whose name
starts with ``allauth.socialaccount.providers.`` is found in
``INSTALLED_APPS``.

Set this to ``True`` explicitly when using custom or third-party allauth
provider apps that do not follow the ``allauth.socialaccount.providers.*``
namespace convention, so that their ``SocialApp`` credentials can be
managed in the Django admin.

.. code-block:: python

    OPENWISP_USERS_SOCIALACCOUNT_ADMIN_NEEDED = True

.. _openwisp_users_auth_api:

``OPENWISP_USERS_AUTH_API``
---------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the :doc:`rest-api` is enabled or not.

``OPENWISP_USERS_AUTH_THROTTLE_RATE``
-------------------------------------

============ ===========
**type**:    ``str``
**default**: ``100/day``
============ ===========

Indicates the rate throttling for the :ref:`obtain_auth_token` API
endpoint.

Please note that the current rate throttler is very basic and will also
count valid requests for rate limiting. For more information, check
Django-rest-framework `throttling guide
<https://www.django-rest-framework.org/api-guide/throttling/>`_.

.. _openwisp_users_auth_backend_auto_prefixes:

``OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES``
---------------------------------------------

============ ===========
**type**:    ``tuple``
**default**: ``tuple()``
============ ===========

A tuple or list of international prefixes which will be automatically
tested by :ref:`the authentication backend of OpenWISP Users
<UsersAuthenticationBackend>` when parsing phone numbers.

Each prefix will be prepended to the username string automatically and
parsed with the ``phonenumbers`` library to find out if the result is a
valid number of not.

This allows users to log in by using only the national phone number,
without having to specify the international prefix.

.. _openwisp_users_export_users_command_config:

``OPENWISP_USERS_EXPORT_USERS_COMMAND_CONFIG``
----------------------------------------------

============ ==========================================================================
**type**:    ``dict``
**default**: .. code-block:: python

                 {
                     "fields": [
                         "id",
                         "username",
                         "email",
                         "password",
                         "first_name",
                         "last_name",
                         "is_staff",
                         "is_active",
                         "date_joined",
                         "phone_number",
                         "birth_date",
                         "location",
                         "notes",
                         "language",
                         {
                             "name": "organizations",
                             "callable": openwisp_users.settings._export_organizations,
                         },
                     ],
                     "select_related": [],
                     "prefetch_related": [],
                 }
============ ==========================================================================

.. note::

    The ``callable`` value must be a Python callable (function or method),
    not a string path. Ensure the function is imported in your settings
    file before referencing it.

This setting configures the fields exported by the :ref:`export_users`
management command.

Field definitions
~~~~~~~~~~~~~~~~~

Each entry in ``fields`` can be either:

- A string, representing a direct attribute of the user model:

  .. code-block:: python

      "email"

- A dictionary, allowing advanced customization:

  .. code-block:: python

      {
          "name": "organizations",
          "callable": my_custom_function,
      }

The following keys are supported in field dictionaries:

- ``name`` (str): the field name used as the CSV column header.
- ``callable`` (callable, optional): a function that takes the user
  instance as input and returns the value to be exported.
- ``fields`` (list of str, optional): a list of attributes to extract from
  a related object or queryset.

Priority order:

- If ``callable`` is provided, it is used.
- Else if ``fields`` is provided, the related object(s) are serialized.
- Otherwise, the value is resolved using ``name``.

Related objects
~~~~~~~~~~~~~~~

You can export fields from related models in two ways:

- **Dot notation** (for ``ForeignKey`` or ``OneToOne``):

  .. code-block:: python

      "profile.phone_number"

- **Structured extraction using ``fields``**:

  .. code-block:: python

      {
          "name": "groups",
          "fields": ["name"],
      }

If the attribute resolves to a queryset (e.g. reverse ``ForeignKey`` or
``ManyToMany``), multiple values are serialized into a single CSV cell.

Query optimization
~~~~~~~~~~~~~~~~~~

- ``select_related`` can be used for ``ForeignKey`` and ``OneToOne``
  relations.
- ``prefetch_related`` can be used for reverse relations and
  ``ManyToMany`` fields.

Example:

.. code-block:: python

    {
        "fields": [
            "username",
            "email",
            "profile.phone_number",
            {
                "name": "groups",
                "fields": ["name"],
            },
        ],
        "select_related": ["profile"],
        "prefetch_related": ["groups"],
    }

.. _openwisp_users_user_password_expiration:

``OPENWISP_USERS_USER_PASSWORD_EXPIRATION``
-------------------------------------------

============ ===========
**type**:    ``integer``
**default**: ``0``
============ ===========

Number of days after which a user's password will expire. In other words,
it determines when users will be prompted to change their passwords.

If set to ``0``, this feature is disabled, and users are not required to
change their passwords.

.. _openwisp_users_staff_user_password_expiration:

``OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION``
-------------------------------------------------

============ ===========
**type**:    ``integer``
**default**: ``0``
============ ===========

Similar to :ref:`OPENWISP_USERS_USER_PASSWORD_EXPIRATION`, but for **staff
users**.
