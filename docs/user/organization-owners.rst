Organization Owners
-------------------

An organization owner is a user who is designated as the owner
of a particular organization and this owner can not be deleted
or edited by other administrators, only superusers have the permission to do this.

By default, the first manager of an organization is designated as the owner of that organization.

If the ``OrganizationUser`` instance related to the owner of an organization is deleted
or flagged as ``is_admin=False``, the admin interface will return an error informing
users that the operation is not allowed, the owner should be changed before attempting to do that.

