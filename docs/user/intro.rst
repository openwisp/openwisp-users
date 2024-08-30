Users: Structure & Features
===========================

The OpenWISP Users module leverages the capabilities of the `Django
Framework <https://djangoproject.com/>`_ and its rich ecosystem to provide
OpenWISP with features for managing user accounts, permission groups,
supporting different authentication schemes, and implementing
multi-tenancy. This allows multiple organizations to be managed by
different users within a single OpenWISP instance, among other
functionalities.

.. contents:: **Summary of the key features available**:
    :depth: 2
    :local:

User Management
---------------

- Create, read, update, and delete user accounts.
- Support for custom user fields through extensible models (see
  :doc:`../developer/extending` for more information).
- :ref:`Export user data <export_users>` through a management command
  (from the Linux shell).

Multi-tenancy
-------------

- Create multiple organizations (also commonly referred to as tenants).
- Users can be associated with one or multiple organizations as members,
  managers, or owners.
- Each organization can access only their data.
- Shared data: some objects can be shared among multiple organizations.

See :doc:`basic-concepts` for more information.

Permissions and Roles
---------------------

- Granular permission control for users and organizations.
- Default roles for administrators, managers, and regular users.
- Customizable permission sets for specific needs.

See :doc:`basic-concepts` for more information.

API Integration
---------------

- RESTful API endpoints for user and organization management.
- Secure API access with token-based authentication.

See :doc:`rest-api` for more information.

Admin Interface
---------------

- User-friendly Django admin interface.
- Customizable admin views for user and organization management (see
  :doc:`../developer/extending` for more information).

Extensible Authentication
-------------------------

With some additional work, it is possible to leverage the rich ecosystem
of Django third party apps to implement the following:

- Possibility to log in in the admin interface via authentication schemes
  like OAuth, SAML, MS Azure Authentication, etc.
- Support multi-factor authentication (MFA).

On a similar note, the :doc:`OpenWISP RADIUS </radius/index>` module ships
logic that allows end-users to log into WiFi services using OAuth (e.g.:
social login provided by Google, Facebook) or SAML (e.g.: `EIDAS
<https://www.eid.as/>`_, `SPID <https://www.spid.gov.it/en/>`_).
