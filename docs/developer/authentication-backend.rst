Authentication Backend
----------------------

.. include:: /partials/developers-docs-warning.rst

The authentication backend in ``openwisp_users.backends.UsersAuthenticationBackend``
allows users to authenticate using their
``email`` or ``phone_number`` instead of their ``username``.
Authenticating with the ``username`` is still allowed,
but ``email`` has precedence.

If the username string passed is parsed as a valid phone number, then
``phone_number`` has precedence.

Phone numbers are parsed using the ``phonenumbers`` library, which means
that even if the user adds characters like spaces, dots or dashes, the number
will be recognized anyway.

When parsing phone numbers, the
`OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES
<#openwisp_users_auth_backend_auto_prefixes>`_
setting allows to specify a list of international prefixes that can
be prepended to the username string automatically in order to allow
users to log in without having to type the international prefix.

The authentication backend can also be used as follows:

.. code-block:: python

    from openwisp_users.backends import UsersAuthenticationBackend

    backend = UsersAuthenticationBackend()
    backend.authenticate(request, identifier, password)
