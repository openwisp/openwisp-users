Miscellaneous Utilities
=======================

.. include:: ../partials/developer-docs.rst

This section covers miscellaneous utilities provided by the OpenWISP Users
module.

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

Organization Membership Helpers
-------------------------------

The ``User`` model offers methods to efficiently check whether the user is
a member, manager, or owner of an organization.

Use these methods to distinguish between different user roles across
organizations and minimize database queries.

.. code-block:: python

    import swapper

    User = swapper.load_model("openwisp_users", "User")
    Organization = swapper.load_model("openwisp_users", "Organization")

    user = User.objects.first()
    org = Organization.objects.first()
    user.is_member(org)
    user.is_manager(org)
    user.is_owner(org)

    # Also valid (avoids query to retrieve Organization instance)
    device = Device.objects.first()
    user.is_member(device.organization_id)
    user.is_manager(device.organization_id)
    user.is_owner(device.organization_id)

``is_member(org)``
~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is a member of the specified ``Organization``
instance. Alternatively, you can pass a ``UUID`` or ``str`` representing
the organization's primary key, which allows you to avoid an additional
database query to fetch the organization instance.

Use this check to grant access to end-users who need to consume services
offered by organizations they're members of, such as authenticating to
public WiFi services.

``is_manager(org)``
~~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is a member of the specified ``Organization``
instance and has the ``OrganizationUser.is_admin`` field set to ``True``.
Alternatively, you can pass a ``UUID`` or ``str`` representing the
organization's primary key, which allows you to avoid an additional
database query to fetch the organization instance.

Use this check to grant access to managers of organizations, who need to
perform administrative tasks such as creating, editing, or deleting
objects of their organization, or accessing sensitive information like
firmware images.

``is_owner(org)``
~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is a member of the specified ``Organization``
instance and is the owner of the organization, checked against the
presence of an ``OrganizationOwner`` instance for the user. Alternatively,
you can pass a ``UUID`` or ``str`` representing the organization's primary
key, which allows you to avoid an additional database query to fetch the
organization instance.

Use this check to prevent managers from taking control of organizations
without the original owner's consent.

``organizations_dict``
~~~~~~~~~~~~~~~~~~~~~~

The methods described above utilize the ``organizations_dict`` property
method, which builds a dictionary containing the primary keys of
organizations the user is a member of, along with information about
whether the user is a manager (``is_admin``) or owner (``is_owner``).

This data structure is cached automatically to prevent multiple database
queries across multiple requests.

The cache is automatically invalidated on the following events:

- An ``OrganizationUser`` is added, changed, or deleted.
- An ``OrganizationOwner`` is added, changed, or deleted.
- The ``is_active`` field of an ``Organization`` changes.

Usage example:

.. code-block::

    >>> user.organizations_dict
    ... {'20135c30-d486-4d68-993f-322b8acb51c4': {'is_admin': True, 'is_owner': False}}
    >>> user.organizations_dict.keys()
    ... dict_keys(['20135c30-d486-4d68-993f-322b8acb51c4'])

``organizations_managed``
~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a list of primary keys of organizations the user can manage.

Usage example:

.. code-block::

    >>> user.organizations_managed
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

``organizations_owned``
~~~~~~~~~~~~~~~~~~~~~~~

Returns a list of primary keys of organizations the user owns.

Usage example:

.. code-block::

    >>> user.organizations_owned
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

.. _usersauthenticationbackend:

``UsersAuthenticationBackend``
------------------------------

**Full python path**:
``openwisp_users.backends.UsersAuthenticationBackend``.

This authentication backend enables users to authenticate using their
email or phone number, as well as their username. Email authentication
takes precedence over the username, while phone number authentication
takes precedence if the identifier passed as argument is a valid phone
number.

Phone numbers are parsed using the `phonenumbers
<https://github.com/daviddrysdale/python-phonenumbers>`_ library, ensuring
recognition even if users include characters like spaces, dots, or dashes.

The :ref:`OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES
<openwisp_users_auth_backend_auto_prefixes>` setting allows specifying a
list of international prefixes that can be automatically prepended to the
username string, enabling users to log in without typing the international
prefix.

Additionally, the backend supports phone numbers with a leading zero,
ensuring successful authentication even with the leading zero included.

You can also use the backend programmatically:

.. code-block:: python

    from openwisp_users.backends import UsersAuthenticationBackend

    backend = UsersAuthenticationBackend()
    backend.authenticate(request, identifier, password)

``PasswordExpirationMiddleware``
--------------------------------

**Full python path**:
``openwisp_users.middleware.PasswordExpirationMiddleware``.

When the password expiration feature is enabled (see
:ref:`OPENWISP_USERS_USER_PASSWORD_EXPIRATION` and
:ref:`OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION`), this middleware
restricts users to the *password change view* until they change their
password.

Ensure this middleware follows ``AuthenticationMiddleware`` and
``MessageMiddleware``:

.. code-block:: python

    # in your_project/settings.py
    MIDDLEWARE = [
        # Other middlewares
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "openwisp_users.middleware.PasswordExpirationMiddleware",
    ]

``PasswordReuseValidator``
--------------------------

**Full python path**:
``openwisp_users.password_validation.PasswordReuseValidator``.

On password change views, this validator ensures users cannot reuse their
current password as the new password.

Add the validator to the ``AUTH_PASSWORD_VALIDATORS`` Django setting:

.. code-block:: python

    # in your-project/settings.py
    AUTH_PASSWORD_VALIDATORS = [
        # Other password validators
        {
            "NAME": "openwisp_users.password_validation.PasswordReuseValidator",
        },
    ]
