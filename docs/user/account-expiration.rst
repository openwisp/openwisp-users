Account Expiration
==================

OpenWISP Users supports account expiration to help administrators manage
accounts that are meant to stay active only for a limited period of time.

Use cases
---------

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

How it works
------------

When an ``expiration_date`` is set on a user account, OpenWISP Users can
send reminder emails before the account expires. The reminder period can
be configured using :ref:`OPENWISP_USERS_EXPIRATION_WARNING_DAYS
<openwisp_users_expiration_warning_days>`.

Once the expiration date is reached, the account is automatically
deactivated unless the expiration date is extended or removed.
