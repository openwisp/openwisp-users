Account and Password Expiration
===============================

.. contents:: **Table of contents**:
    :depth: 2
    :local:

.. _account_expiration:

Account Expiration
------------------

Account expiration is an account lifecycle policy enforced on a
case-by-case basis by setting an expiration date on individual users.

Use Cases
~~~~~~~~~

One common use case is contractor access. A contractor may be responsible
for a specific part of the network only for the duration of a contract, so
the user's ``expiration_date`` can mirror the contract expiration date.
This reduces the amount of manual follow-up needed from the main
administrators, who do not have to keep checking whether temporary
contractor accounts should still be active.

Another common use case is temporary WiFi access created through
:doc:`OpenWISP RADIUS batch user generation
</radius/user/generating_users>`. In that scenario, user accounts are
created for short-lived access windows, such as events, guest access, or
other time-bound connectivity needs.

How Account Expiration Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an ``expiration_date`` is set on a user account, OpenWISP Users can
send reminder emails before the account expires. The reminder period can
be configured using :ref:`OPENWISP_USERS_EXPIRATION_WARNING_DAYS
<openwisp_users_expiration_warning_days>`.

Once the expiration date has passed, the account is automatically
deactivated unless the expiration date is extended or removed.

.. _password_expiration:

Password Expiration
-------------------

Password expiration is a global expiration policy that requires users to
change their password after a configured number of days.

Use cases
~~~~~~~~~

Password expiration is useful for organizations that have an internal
password policy for security reasons and need to enforce the same policy
in their network management systems and/or network services.

How password expiration works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When password expiration is enabled, OpenWISP Users checks the age of each
user's password and notifies users before their password expires.

Password expiration can be configured separately for regular users and
staff users:

- :ref:`OPENWISP_USERS_USER_PASSWORD_EXPIRATION
  <openwisp_users_user_password_expiration>` controls password expiration
  for regular users.
- :ref:`OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION
  <openwisp_users_staff_user_password_expiration>` controls password
  expiration for staff users.

If either setting is set to ``0``, password expiration is disabled for
that user type.

OAuth / SAML logins and password expiration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sessions authenticated via an external method (SAML, OAuth, etc.) are
**exempt** from password expiration enforcement. Even if the user's local
password has expired, the user is not blocked as long as the session is
marked as externally authenticated.

REST API behavior
~~~~~~~~~~~~~~~~~

When a password-authenticated session has expired, REST API clients
receive a machine-readable JSON ``403`` response instead of an HTTP
redirect. The response body includes a ``password_expired`` error code and
a URL pointing to the web password-change page. The
``api_password_change_url`` and ``api_password_reset_url`` fields are also
included, but only when :ref:`OpenWISP Users' REST API is enabled
<openwisp_users_auth_api>`:

.. code-block:: json

    {
        "detail": "Your password has expired. Update it to continue.",
        "code": "password_expired",
        "web_password_change_url": "https://example.org/accounts/password/change/",
        "api_password_change_url": "https://example.org/api/v1/users/user/password/change/",
        "api_password_reset_url": "https://example.org/api/v1/users/password/reset/"
    }
