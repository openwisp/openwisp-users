REST API
========

.. contents:: **Table of contents**:
    :depth: 1
    :local:

.. note::

    The REST API is enabled by default but can be disabled by setting
    :ref:`OPENWISP_USERS_AUTH_API` to ``False``.

.. _users_live_documentation:

Live Documentation
------------------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/live-api-docs.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/live-api-docs.png
    :alt: Live API Documentation

General live API documentation, following the OpenAPI specification, is
available at ``/api/v1/docs/``.

.. _users_browsable_web_interface:

Browsable Web Interface
-----------------------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/api-ui.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/api-ui.png
    :alt: Browsable REST API Web Interface

Additionally, opening any of the endpoints listed below directly in the
browser will show the `browsable API interface of Django-REST-Framework
<https://www.django-rest-framework.org/topics/browsable-api/>`_, which
makes it even easier to find out the details of each endpoint.

.. _obtain_auth_token:

Obtain Authentication Token
---------------------------

.. code-block:: text

    /api/v1/users/token/

This endpoint only accepts the ``POST`` method and is used to retrieve the
Bearer token that is required to make API requests to other endpoints.

Example usage:

.. code-block:: shell

    curl -i -X POST http://localhost:8000/api/v1/users/token/ -d "username=openwisp" -d "password=1234"

    HTTP/1.1 200 OK
    Date: Wed, 05 Jun 2024 16:31:33 GMT
    Server: WSGIServer/0.2 CPython/3.8.10
    Content-Type: application/json
    Vary: Accept
    Allow: POST, OPTIONS
    X-Frame-Options: DENY
    Content-Length: 52
    X-Content-Type-Options: nosniff
    Referrer-Policy: same-origin
    Cross-Origin-Opener-Policy: same-origin

    {"token": "7a2e1d3d008253c123c61d56741003db5a194256"}

.. _authenticating_rest_api:

Authenticating with the User Token
----------------------------------

The authentication class
``openwisp_users.api.authentication.BearerAuthentication`` is used across
the different OpenWISP modules for authentication.

To use it, first of all get the user token as described above in
:ref:`obtain_auth_token`, then send the token in the ``Authorization``
header:

.. code-block:: shell

    # Get the bearer token
    TOKEN=$(curl -X POST http://localhost:8000/api/v1/users/token/ -d "username=openwisp" -d "password=1234" | jq -r .token)

    # Get user list, send bearer token in authorization header
    curl http://localhost:8000/api/v1/users/user/ -H "Authorization: Bearer $TOKEN"

List of Endpoints
-----------------

For complete parameter details, see the :ref:`users_live_documentation`
and the :ref:`users_browsable_web_interface` of each endpoint.

.. _user_password_reset:

Request Password Reset
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/password/reset/

For an eligible user, this endpoint sends a password reset e-mail when the
``input`` parameter matches a username, e-mail address or phone number.

Unknown or ineligible identifiers receive the same response without an
e-mail, so this endpoint cannot be used to find out whether an identifier
is registered.

Example usage:

.. code-block:: shell

    curl -i -X POST http://localhost:8000/api/v1/users/password/reset/ -d "input=openwisp"

.. _user_password_reset_confirm:

Confirm Password Reset
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/password/reset/confirm/

Sets a new password given the ``uid`` and ``token`` received in the
password reset e-mail, along with ``new_password1`` and ``new_password2``.

Example usage:

.. code-block:: shell

    curl -i -X POST http://localhost:8000/api/v1/users/password/reset/confirm/ \
        -d "uid=<uid>" -d "token=<token>" \
        -d "new_password1=newpass123" -d "new_password2=newpass123"

.. _user_password_change:

Change Own Password
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/user/password/change/

Lets an authenticated user change their own password, given their
``old_password`` and a new one (``new_password1``, confirmed via
``new_password2``). Unlike :ref:`Change User Password
<change_user_password>` below, this endpoint always operates on the
requesting user.

Example usage:

.. code-block:: shell

    curl -i -X POST http://localhost:8000/api/v1/users/user/password/change/ \
        -H "Authorization: Bearer $TOKEN" \
        -d "old_password=oldpass123" \
        -d "new_password1=newpass123" \
        -d "new_password2=newpass123"

.. _change_user_password:

Change User Password
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/password/

Allows an authorized user to change another user's password. The ``id``
identifies the user whose password is changed.

List Groups
~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/group/

Create New Group
~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/group/

Get Group Detail
~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/group/{id}/

Change Group Detail
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/group/{id}/

Patch Group Detail
~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/group/{id}/

Delete Group
~~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/group/{id}/

List Email Addresses
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/email/

Add Email Address
~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST/api/v1/users/user/{id}/email/

Get Email Address
~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/email/{id}/

Change Email Address
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/email/{id}/

Patch Email Address
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/email/{id}/

Make/Unmake Email Address Primary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/email/{id}/

Mark/Unmark Email Address as Verified
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/email/{id}/

Remove Email Address
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/user/{id}/email/{id}/

List Organization Memberships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/organization-membership/

Add Organization Membership
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/user/{id}/organization-membership/

.. note::

    The organization manager flag is represented internally by the
    ``is_admin`` field in the payload.

Get Organization Membership
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/organization-membership/{org_id}/

Change Organization Membership
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/organization-membership/{org_id}/

Patch Organization Membership
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/organization-membership/{org_id}/

Remove Organization Membership
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/user/{id}/organization-membership/{org_id}/

List Organizations
~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/organization/

Create new Organization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/organization/

Get Organization Detail
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/organization/{id}/

Change Organization Detail
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/organization/{id}/

Patch Organization Detail
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/organization/{id}/

Delete Organization
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/organization/{id}/

List Users
~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/

Create User
~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/user/

.. note::

    Passing ``true`` to the optional ``is_verified`` field allows creating
    users with their email address flagged as verified. This will also
    skip sending the verification link to their email address.

    When creating organization memberships, the organization manager flag
    is represented internally by the ``is_admin`` field in the
    ``organization_users`` payload.

Get User Detail
~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/

Change User Detail
~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/

.. note::

    When editing organization memberships, the organization manager flag
    is represented internally by the ``is_admin`` field in the
    ``organization_users`` payload.

Patch User Detail
~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/

.. note::

    When patching organization memberships, the organization manager flag
    is represented internally by the ``is_admin`` field in the
    ``organization_users`` payload.

Delete User
~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/user/{id}/
