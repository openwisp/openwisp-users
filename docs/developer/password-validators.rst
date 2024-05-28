Password Validators
===================

.. include:: ../partials/developer-docs.rst

``openwisp_users.password_validation.PasswordReuseValidator``
-------------------------------------------------------------

On password change views, the ``PasswordReuseValidator`` ensures that users cannot use
their current password as the new password.

You need to add the validator to ``AUTH_PASSWORD_VALIDATORS`` Django setting as shown
below:

.. code-block:: python

    # in your-project/settings.py
    AUTH_PASSWORD_VALIDATORS = [
        # Other password validators
        {
            "NAME": "openwisp_users.password_validation.PasswordReuseValidator",
        },
    ]
