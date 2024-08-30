Basic Concepts
==============

.. contents:: **Table of contents**:
    :depth: 2
    :local:

Superusers
----------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/superuser.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/superuser.png
    :alt: Superuser status flag

A superuser, also known as a "super administrator," is a special type of
admin user account with full access to all aspects of an OpenWISP
instance.

The **Superuser status** flag in the user details page indicates whether a
user is a superuser or not. Only superusers are allowed to edit this flag.

Superusers have all permissions enabled by default and can create, manage
and delete any organization available in the system.

However, it's essential to use superuser accounts sparingly due to their
elevated privileges.

To grant access to specific features and organizations within your
OpenWISP system, consider creating staff users without the "superuser
status" flag enabled. Assign them to one of the available permission
groups, as explained in the following sections. These users will have
limited administrative capabilities, managing only the objects permitted
by their assigned permissions and associated organization.

Staff Users
-----------

Users with the **Staff status** flag enabled, as shown in the screenshot
above, have access to the OpenWISP Admin interface. This access allows
them to manage various aspects of the OpenWISP instance according to their
assigned permissions and organizational role.

Users with this flag disabled will still be able to interact with
OpenWISP, but in a more limited way. They can use non-administrative user
interfaces or specific REST API HTTP endpoints designed for end-users.

.. note::

    An example of an end-user is someone who signs up for a public WiFi
    hotspot service via the :doc:`WiFi Login Pages
    </wifi-login-pages/index>` module. This optional OpenWISP module is
    commonly used in public WiFi hotspot deployments.

Permissions
-----------

The permission system used by OpenWISP is based on the `Django Permission
System
<https://docs.djangoproject.com/en/4.2/topics/auth/default/#permissions-and-authorization>`_.

In short, a permission indicates whether a user has the authority to
perform the following operations:

- **View**: Access the details of a specific class of objects, e.g., view
  the details of users.
- **Add**: Create a new object of a specific class, e.g., add a new user.
- **Change**: Edit the details of a specific class, e.g., modify existing
  user details.
- **Delete**: Remove an object of a specific class, e.g., delete users.

.. note::

    For more detailed technical information, please refer to the `Django
    Documentation
    <https://docs.djangoproject.com/en/4.2/topics/auth/default/>`_.

.. _default_permission_groups:

Default Permission Groups
-------------------------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/permission-groups.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/permission-groups.png
    :alt: Default Permission Groups of OpenWISP

A permission group is a collection of permissions that can be assigned to
multiple users.

It is then possible to change the permissions on the group to reflect the
changes on all the users who are part of the permission group.

This allows to avoid having to assign permissions to individual users,
which is hard to maintain and leads to inconsistent permission
configuration over time.

OpenWISP provides a few permission groups which are explained below.

Administrator
~~~~~~~~~~~~~

This permission group is designed for users who need to manage most
aspects of an organization without having superuser access.

Operator
~~~~~~~~

This permission group is designed for users who need to be able to perform
a limited amount of operations like provisioning new devices and perform
regular network maintenance operations but are not allowed to create new
users or change the permissions settings of other users.

Use this for users who have very specific and limited responsibilities in
the network.

Organizations & Multi-Tenancy
-----------------------------

The concept of multi-tenancy in OpenWISP is implemented through
"organizations".

An organization in OpenWISP represents a distinct entity or tenant within
the system. Each organization has its own set of users, configurations,
data, and administrative controls, allowing for isolation and management
of network resources.

Key Features of Organizations:

- **Isolation & Privacy**: Organizations provide a logical separation of
  resources, ensuring that data and configurations are segregated between
  different entities or tenants. Each tenant can only see and interact
  with the data of their organizations and :ref:`shared_objects` defined
  by super administrators.
- **User Management**: Each organization can have its own set of users
  with specific roles and permissions tailored to their responsibilities
  within that organization.
- **Administrative Controls**: Super administrators can define, oversee,
  and manage :ref:`shared_objects`, permission policies, and any other
  processes relating to organizations to ensure consistency across the
  entire system.

By leveraging organizations, OpenWISP provides a robust framework for
implementing multi-tenancy, allowing for the efficient management of
network resources across diverse entities or tenants within a single
instance of the platform.

.. note::

    Multi-Tenancy and Organizations are implemented in OpenWISP with the
    `django-organizations
    <https://github.com/bennylope/django-organizations>`_ third-party app.

Organization Membership and Roles
---------------------------------

A user can be associated to one or multiple organizations and have
different roles in each.

Here's a summary of the default organization roles.

Organization Manager
~~~~~~~~~~~~~~~~~~~~

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/org-manager.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/org-manager.png
    :alt: Organization Manager

Any user with the "Is admin" flag enabled for a specific organization (as
shown in the screenshot above) is considered by the system a manager of
that organization. Organization managers have the authority to view and
interact with the data belonging to that organization according to their
set of permissions (as defined in :ref:`Permission Groups
<default_permission_groups>`).

To modify this flag, navigate to the "ORGANIZATION USERS" section on the
"Change user" page.

Organization Members (End-Users)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/org-member.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/org-member.png
    :alt: Organization Member

Any user with the "Is admin" flag disabled for a specific organization (as
shown in the screenshot above) is considered by the system a regular
end-user of that organization.

These users are consumers of a service provided by the organization. They
will not be able to see or interact with any object of that organization
via the administrative interface, even if they are flagged as Staff users.

They can only consume REST API endpoints or other non administrative user
interface pages.

A real-world example of this is the :ref:`User API endpoints of OpenWISP
RADIUS <radius_user_api_endpoints>`, which allow users to sign up to an
organization, verify their phone number by receiving a verification code
via SMS, see their RADIUS sessions, etc. All those endpoints are tied to
an organization because different organizations can have very different
configurations. Users are allowed to consume those endpoints only if
they're members.

.. _organization_owners:

Organization Owners
~~~~~~~~~~~~~~~~~~~

An organization owner is a user designated as the owner of a particular
organization. This owner cannot be deleted or edited by other
administrators; only superusers have permission to perform these actions.

By default, the first manager of an organization is designated as the
owner of that organization.

Only superusers and organization owners are allowed to change the owner of
an organization. Organization owners can be changed from the "Change
organization" page by navigating to the "ORGANIZATION OWNER" section.

If the ``OrganizationUser`` instance related to the owner of an
organization is deleted or flagged as ``is_admin=False``, the admin
interface will return an error informing users that the operation is not
allowed. The owner should be changed before attempting to perform such
actions.

.. _shared_objects:

Shared Objects
--------------

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/shared-object.png
    :target: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/shared-object.png
    :alt: Shared Object

A shared object is a resource that can be used by multiple organizations
or tenants within the system.

Shared objects do not belong to any specific organization. In the user
interface, the organization field is empty, and it displays *"Shared
systemwide (no organization)"* as shown in the screenshot above. These
objects are defined and managed by super administrators and can include
configurations, policies, or other data that need to be consistent across
all organizations.

By sharing common resources, global uniformity and consistency can be
enforced across the entire system.

.. note::

    Only a specific subset of object classes can be shared. You can
    determine if an object can be shared by attempting to create a new
    object for that class while logged in as a superuser. If the
    organization field shows the option *"Shared systemwide (no
    organization)"*, it means the object can be shared.

Examples of shared objects include:

- :ref:`Shared Configuration Templates <controller_shared_vs_org>`
- Shared VPN servers
- Shared Subnets
