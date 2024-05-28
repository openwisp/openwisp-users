Middlewares
===========

.. include:: ../partials/developer-docs.rst

``openwisp_users.middleware.PasswordExpirationMiddleware``
----------------------------------------------------------

When password expiration feature is on (see `OPENWISP_USERS_USER_PASSWORD_EXPIRATION
<#openwisp-users-user-password-expiration>`_ and
`OPENWISP_USERS_STAFF_USER_PASSWORD_EXPIRATION
<#openwisp-users-staff-user-password-expiration>`_), this middleware confines the user
to the *password change view* until they change their password.

This middleware should come after ``AuthenticationMiddleware`` and
``MessageMiddleware``, as following:

.. code-block:: python

    # in your_project/settings.py
    MIDDLEWARE = [
        # Other middlewares
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "openwisp_users.middleware.PasswordExpirationMiddleware",
    ]
