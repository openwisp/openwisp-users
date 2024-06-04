REST API
========

.. note::

    The REST API is enabled by default but can be disabled by setting
    :ref:`OPENWISP_USERS_AUTH_API` to ``False``.

Live documentation
------------------

A general live API documentation (following the OpenAPI specification) at
``/api/v1/docs/``.

Browsable Web Interface
-----------------------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/api-ui.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/api-ui.png
    :alt: Browsable REST API Web Interface

Additionally, opening any of the endpoints listed below directly in the browser will
show the `browsable API interface of Django-REST-Framework
<https://www.django-rest-framework.org/topics/browsable-api/>`_, which makes it even
easier to find out the details of each endpoint.

Obtain Authentication Token
---------------------------

.. code-block:: text

    /api/v1/users/token/

This endpoint only accepts the ``POST`` method and is used to retrieve the Bearer token
that is required to make API requests to other endpoints.

Example usage of the endpoint:

.. code-block:: shell

    http POST localhost:8000/api/v1/users/token/ username=openwisp password=1234

    HTTP/1.1 200 OK
    Allow: POST, OPTIONS
    Content-Length: 52
    Content-Type: application/json
    Date: Wed, 13 May 2020 10:59:34 GMT
    Server: WSGIServer/0.2 CPython/3.6.9
    Vary: Cookie
    X-Content-Type-Options: nosniff
    X-Frame-Options: DENY

    {
        "token": "7a2e1d3d008253c123c61d56741003db5a194256"
    }

.. _authenticating_rest_api:

Authenticating with the user token
----------------------------------

The authentication class ``openwisp_users.api.authentication.BearerAuthentication`` is
used across the different OpenWISP modules for authentication.

To use it, first of all get the user token as described above in `Obtain Authentication
Token <#obtain-authentication-token>`_, then send the token in the ``Authorization``
header:

.. code-block:: shell

    # get token
    TOKEN=$(http POST :8000/api/v1/users/token/ username=openwisp password=1234 | jq -r .token)

    # send bearer token
    http GET localhost:8000/api/v1/firmware-upgrader/build/ "Authorization: Bearer $TOKEN"

List of endpoints
-----------------

Since the detailed explanation is contained in the `Live documentation
<#live-documentation>`_ and in the `Browsable web page <#browsable-web-interface>`_ of
each point, here we'll provide just a list of the available endpoints, for further
information please open the URL of the endpoint in your browser.

Change User password
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/password/

List Groups
~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/group/

Create new Group
~~~~~~~~~~~~~~~~

.. code-block:: text

    POST /api/v1/users/group/

Get Group detail
~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/group/{id}/

Change Group detail
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/group/{id}/

Patch Group detail
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

Get Organization detail
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/organization/{id}/

Change Organization detail
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/organization/{id}/

Patch Organization detail
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

**Note**: Passing ``true`` to the optional ``is_verified`` field allows creating users
with their email address flagged as verified. This will also skip sending the
verification link to their email address.

Get User detail
~~~~~~~~~~~~~~~

.. code-block:: text

    GET /api/v1/users/user/{id}/

Change User detail
~~~~~~~~~~~~~~~~~~

.. code-block:: text

    PUT /api/v1/users/user/{id}/

Patch User detail
~~~~~~~~~~~~~~~~~

.. code-block:: text

    PATCH /api/v1/users/user/{id}/

Delete User
~~~~~~~~~~~

.. code-block:: text

    DELETE /api/v1/users/user/{id}/
