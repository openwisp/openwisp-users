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

Since the detailed explanation is contained in the
:ref:`users_live_documentation` and in the
:ref:`users_browsable_web_interface` of each endpoint, here we'll provide
just a list of the available endpoints, for further information please
open the URL of the endpoint in your browser.

Change User password
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/password/

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

Get User Detail
~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/

Change User Detail
~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/

Patch User Detail
~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/

Delete User
~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/user/{id}/
