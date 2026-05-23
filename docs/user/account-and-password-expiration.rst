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

Once the expiration date is reached, the account is automatically
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
