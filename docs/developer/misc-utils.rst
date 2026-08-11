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

.. code-block:: python-console

    >>> user.organizations_dict
    ... {'20135c30-d486-4d68-993f-322b8acb51c4': {'is_admin': True, 'is_owner': False}}
    >>> user.organizations_dict.keys()
    ... dict_keys(['20135c30-d486-4d68-993f-322b8acb51c4'])

``organizations_managed``
~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a list of primary keys of organizations the user can manage.

Usage example:

.. code-block:: python-console

    >>> user.organizations_managed
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

``organizations_owned``
~~~~~~~~~~~~~~~~~~~~~~~

Returns a list of primary keys of organizations the user owns.

Usage example:

.. code-block:: python-console

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

``record_password_based_login()``
---------------------------------

**Full python path**: ``openwisp_users.auth.record_password_based_login``.

Records on the current session, whether the user logged in using the local
password. The ``password_based`` argument is a boolean: ``True`` if the
local password was used, ``False`` for any other authentication method
(SAML, OAuth, etc.).

This is used internally by authentication flows to record how the session
was authenticated. Sessions marked as not password-based are exempt from
password expiration enforcement.

.. code-block:: python

    from openwisp_users.auth import record_password_based_login

    # After a successful SAML or OAuth login
    record_password_based_login(request, False)

``create_auth_token()``
-----------------------

**Full python path**: ``openwisp_users.auth.create_auth_token``.

Creates or renews a DRF authentication token and records whether the token
was obtained using the user's local password in
``User.password_based_token``.

This is the recommended helper for downstream apps issuing authentication
tokens. It determines how the request was authenticated, creates or renews
the token, and records its provenance in a single call. Callers therefore
do not need to manage ``password_based_token`` themselves.

The token is considered password-based when:

- the request has no authenticated user, or its user differs from the user
  receiving the token. This indicates that local credentials were
  validated directly, as in a login endpoint;
- the request was not authenticated using a passwordless method, such as a
  sesame magic-link token; and
- the request's Django session is marked as password-based by
  ``record_password_based_login()`` (see below).

Pass ``renew=True`` to delete the user's existing token before creating a
new one. This ensures the returned token always has a new key.

.. code-block:: python

    from openwisp_users.auth import create_auth_token

    token = create_auth_token(request, user)
    rotated_token = create_auth_token(request, user, renew=True)

``is_password_based_user()``
----------------------------

**Full python path**: ``openwisp_users.auth.is_password_based_user``.

Returns whether the last authentication token issued to a user was
obtained using the local password. ``None`` is treated as password-based
for backward compatibility. Use this helper instead of reading
``password_based_token`` directly.

.. code-block:: python

    from openwisp_users.auth import is_password_based_user

    is_password_based_user(user)

``is_password_based_login()``
-----------------------------

**Full python path**: ``openwisp_users.auth.is_password_based_login``.

Returns whether the local password was used to authenticate. It checks DRF
token provenance first, then the session marker, and finally the user's
stored value. Missing provenance remains password-based for backward
compatibility.

.. code-block:: python

    from openwisp_users.auth import is_password_based_login

    is_password_based_login(request)
    is_password_based_login(user=user)

``PasswordExpirationMiddleware``
--------------------------------

**Full python path**:
``openwisp_users.middleware.PasswordExpirationMiddleware``.

When the password expiration feature is enabled (see
:ref:`OPENWISP_USERS_USER_PASSWORD_EXPIRATION` and
:ref:`OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION`), this middleware
restricts users to the *password change view* until they change their
password.

The middleware runs **before** the view: for browser (HTML) requests it
redirects to the password-change page, while for non-exempt DRF endpoints
it returns a JSON ``403`` response with a ``password_expired`` error code
and a link to the password-change API endpoint. The token issuance,
password change, password reset, and password reset confirmation endpoints
are exempt so users can recover access.

Sessions that did not log in with the local password (SAML, OAuth, RADIUS,
etc.) are **exempt**: the middleware does not block them even if the
user's local password has technically expired.

Requests carrying a ``Bearer`` token to a DRF view that supports Bearer
authentication are not blocked by password expiration, even if they also
carry an expired-password session cookie. DRF still validates the token.

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
