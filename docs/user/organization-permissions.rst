Organization permissions
========================

Here's a summary of the default permissions:

- All users who belong to the Administrators group and are organization managers
  (``OrganizationUser.is_admin=True``) have permission to edit the objects related
  to the organizations they administrate.
- Only superusers have permission to add and delete organizations.
- Only superusers and `organization owners <#organization-owners>`_ have permission
  to change the ``OrganizationOwner`` inline or delete the relation.
- Users who are simple members of an organization (``OrganizationUser.is_admin=False``)
  are considered end-users of a service provided by that organization. They do not have
  any permission to change objects via the Django admin for that organization; they can
  only consume API endpoints. A real-world example of this is the `User API endpoints
  of OpenWISP RADIUS
  <https://openwisp-radius.readthedocs.io/en/stable/user/api.html#user-api-endpoints>`_,
  which allow users to sign up to an organization, verify their phone number by
  receiving a verification code via SMS, see their RADIUS sessions, etc. All those
  endpoints are tied to an organization because different organizations can have very
  different configurations. Users are allowed to consume the endpoints only if
  they're members.
