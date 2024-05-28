Authentication Backend
======================

.. include:: ../partials/developer-docs.rst

The authentication backend in ``openwisp_users.backends.UsersAuthenticationBackend``
allows users to authenticate using their ``email`` or ``phone_number`` instead of their
``username``. Authenticating with the ``username`` is still supported, but ``email``
takes precedence.

If the provided username string is parsed as a valid phone number, then ``phone_number``
takes precedence.

Phone numbers are parsed using the `phonenumbers
<https://github.com/daviddrysdale/python-phonenumbers>`_ library, which ensures that
numbers are recognized even if users include characters like spaces, dots, or dashes.

The :ref:`OPENWISP_USERS_AUTH_BACKEND_AUTO_PREFIXES
<openwisp_users_auth_backend_auto_prefixes>` setting allows specifying a list of
international prefixes that can be automatically prepended to the username string,
enabling users to log in without typing the international prefix.

Additionally, the backend supports phone numbers with a leading zero, which is common in
some countries for local numbers. This ensures users can authenticate successfully even
if they include the leading zero.

The authentication backend can also be used programmatically, for example:

.. code-block:: python

    from openwisp_users.backends import UsersAuthenticationBackend

    backend = UsersAuthenticationBackend()
    backend.authenticate(request, identifier, password)
