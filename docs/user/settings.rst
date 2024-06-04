Settings
========

.. include:: /partials/settings-note.rst

``OPENWISP_ORGANIZATION_USER_ADMIN``
------------------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the admin section for managing ``OrganizationUser`` items is enabled
or not.

``OPENWISP_ORGANIZATION_OWNER_ADMIN``
-------------------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the admin section for managing ``OrganizationOwner`` items is enabled
or not.

Find out more information about `organization owners <#organization-owners>`_.

.. _openwisp_users_auth_api:

``OPENWISP_USERS_AUTH_API``
---------------------------

============ ===========
**type**:    ``boolean``
**default**: ``True``
============ ===========

Indicates whether the `REST API <#rest-api>`_ is enabled or not.

``OPENWISP_USERS_AUTH_THROTTLE_RATE``
-------------------------------------

============ ===========
**type**:    ``str``
**default**: ``100/day``
============ ===========

Indicates the rate throttling for the `Obtain Authentication
<#obtain-authentication-token>`_ API endpoint.

Please note that the current rate throttler is very basic and will also count valid
requests for rate limiting. For more information, check Django-rest-framework
`throttling guide <https://www.django-rest-framework.org/api-guide/throttling/>`_.

.. _openwisp_users_auth_backend_auto_prefixes:

``OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES``
---------------------------------------------

============ ===========
**type**:    ``tuple``
**default**: ``tuple()``
============ ===========

A tuple or list of international prefixes which will be automatically tested by `the
authentication backend of openwisp-users <#authentication-backend>`_ when parsing phone
numbers.

Each prefix will be prepended to the username string automatically and parsed with the
``phonenumbers`` library to find out if the result is a valid number of not.

This allows users to log in by using only the national phone number, without having to
specify the international prefix.

.. _openwisp_users_export_users_command_config:

``OPENWISP_USERS_EXPORT_USERS_COMMAND_CONFIG``
----------------------------------------------

============ =============================
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
                         "organizations",
                     ],
                     "select_related": [],
                 }
============ =============================

This setting can be used to configure the exported fields for the :ref:`export_users
<export_users>` command.

The ``select_related`` property can be used to optimize the database query.

``OPENWISP_USERS_USER_PASSWORD_EXPIRATION``
-------------------------------------------

============ ===========
**type**:    ``integer``
**default**: ``0``
============ ===========

Number of days after which a user's password will expire. In other words, it determines
when users will be prompted to change their passwords.

If set to ``0``, this feature is disabled, and users are not required to change their
passwords.

``OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION``
-------------------------------------------------

============ ===========
**type**:    ``integer``
**default**: ``0``
============ ===========

Similar to `OPENWISP_USERS_USER_PASSWORD_EXPIRATION
<#openwisp-users-user-password-expiration>`_, but for **staff users**.
