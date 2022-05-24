Changelog
=========

Version 1.0.1 [2022-05-24]
--------------------------

- Updated fur translations

Version 1.0.0 [2022-03-19]
--------------------------

Features
~~~~~~~~

- Added `UsersAuthenticationBackend class
  <https://github.com/openwisp/openwisp-users#authentication-backend>`_
  that allows users to authenticate using either email, phone_number or username.
- Added the possibility to filter users by their organization in
  the user administration section.
- Added `REST API endpoints for openwisp-users
  <https://github.com/openwisp/openwisp-users#list-of-endpoints>`_.
- Added various `Django REST Framework mixins and utilities
  <https://github.com/openwisp/openwisp-users#django-rest-framework-mixins>`_
  which allow to implement.
- Added `DRF permission classes
  <https://github.com/openwisp/openwisp-users#django-rest-framework-permission-classes>`_.
- Added `passwordless authentication backend for REST APIs
  <https://github.com/openwisp/openwisp-users#2-openwisp_usersapiauthenticationsesameauthentication>`_.
- Added ``OrganizationInvitation`` model.
- Added `email verification success view
  <https://github.com/openwisp/openwisp-users/issues/277>`_.
- Added logout success view.

Changes
~~~~~~~

- `Authentication REST API endpoints are now enabled by default
  <https://github.com/openwisp/openwisp-users#openwisp_users_auth_api>`_.
- Following changes have been made to the User model:

  - Increased max length of `User.location field
    <https://github.com/openwisp/openwisp-users/commit/0088b0bdfe882e54cf6dfd2fbbafa7ccd79a8beb>`_.
  - Added `User.birth_date field
    <https://github.com/openwisp/openwisp-users/issues/221>`_.
  - Added `User.notes field
    <https://github.com/openwisp/openwisp-users/commit/e8b4f0a125969453795a57333e8b2cb612e2743e>`_.
  - Added `User.language field
    <https://github.com/openwisp/openwisp-users/issues/261>`_.
  - Made `User.email case insensitive
    <https://github.com/openwisp/openwisp-users/issues/227>`_.
    Email addresses will always get converted to lower case before
    storage and comparison.

- Updated ``OrganizationOwnerInline`` to use ``raw_id`` field for
  ``organization_user`` field.
- Updated ``OrganizationUserInline`` to use ``autocomplete`` field
  for ``organization`` field.
- **Backward incompatible:** removed `custom permission helpers
  <https://github.com/openwisp/openwisp-users/issues/266>`_.
- **Backward incompatible:** the REST API endpoint ``/api/v1/user/token/``
  has been changed to ``/api/v1/users/token/`` for consistency
  with the rest of the API.

**Dependencies**:

- Dropped support for Django ``2.2.x``.
- Dropped support for Python ``3.6``.
- Added support for Python ``3.8`` and Python ``3.9``.
- Added support for Django ``3.2.x`` and ``4.0.x``.
- Bumped ``django-allauth~=0.46.0``.
- Bumped ``django-organizations~=2.0.1``
- Bumped ``django-phonenumber-field~=6.0.0``.
- Bumped ``openwisp-utils~=1.0.0``.
- Bumped ``swapper~=1.3.0``
- Added ``django-sesame~=2.4.0``.

Bugfixes
~~~~~~~~

- Fixed `internal server error on "/accounts/login/" page
  <https://github.com/openwisp/openwisp-users/issues/218>`_
  when the social account app is disabled.
- Fixed `error on restoring "Group" object with django-reversion
  <https://github.com/openwisp/openwisp-users/issues/214>`_.
- Fixed `error on visiting Django admin URL for non-existing users
  <https://github.com/openwisp/openwisp-users/issues/228>`_.
- Fixed `organization managers could escalate their privileges to superuser
  <https://github.com/openwisp/openwisp-users/issues/284>`_.

Version 0.5.1 [2020-12-13]
--------------------------

Changes
~~~~~~~

- Updated django-allauth to 0.44.x
- Copied the template ``account/login.html`` from django-allauth
  in order to remove the sign up link, which we do not support
- Updated django-extensions to 3.1

Bugfixes
~~~~~~~~

- Updating django-allauth to 0.44.x also fixes an `issue affecting
  OpenWISP Users in production deployment (experienced in ansible-openwisp2)
  <https://github.com/openwisp/ansible-openwisp2/issues/233>`_

Version 0.5.0 [2020-11-18]
--------------------------

Features
~~~~~~~~

N/A.

Changes
~~~~~~~

- [change] Extend ``admin/base_site.html`` in ``confirm_email.html``
- [change] Updated to openwisp-utils 0.7 and switched to new ``register_menu_items``
- [change] Removed typographic error in settings which was maintained
  for backward compatibility
- [change] Removed deprecated ``organizations_pk``

Bugfixes
~~~~~~~~

- [fix] Fix email confirmation when link is invalid
- [docs] Fixed several broken links in "Extend openwisp-users" section
- [fix] Allow swagger to show parameters of obtain token view

Version 0.4.1 [2020-10-08]
--------------------------

- [chores] Allow passing a string or uuid to the
  `Organization membership helpers <https://github.com/openwisp/openwisp-users#organization-membership-helpers>`_
- [fix] The ``OrganizationUser`` instance of an ``OrganizationOwner``
  won't be allowed to be ``is_admin=False``
- [fix] Fixed mutable class attribute in MultitenantAdminMixin
- [fix] Fixed exception when deleting ``OrganizationUser`` of an owner
- [fix] Fixed typographical error in organization name

Version 0.4.0 [2020-08-23]
--------------------------

Features
~~~~~~~~

- [models] Added `organizations_managed <https://github.com/openwisp/openwisp-users#organizations-managed>`_ helper
- [models] Added `organizations_owned <https://github.com/openwisp/openwisp-users#organizations-owned>`_ helper

Changes
~~~~~~~

- [admin]: **Potentially backward incompatible change**:
  Multi-tenant admin classes now allow only org managers.
  Before this version, a user needed to be only org member
  to see items of that organization in the admin, but this
  is wrong! An ``OrganizationUser`` which has ``is_admin=False`` is
  only an end-user of that organization.
  Instead, an ``OrganizationUser`` which has ``is_admin=True`` is
  also a manager and only this type of user shall be allowed
  to manage items of the organization through the django admin site.
  This is needed in order to support users being simple end-users
  in one organization but administrators in others, otherwise
  a staff user who is administrator of one organization would be
  able to change also items of other organizations where
  they are only members and not managers.
- [dependencies] Added support for django 3.1
- [dependencies] django-phonenumber-field 5.0

Version 0.3.1 [2020-08-17]
--------------------------

- [deps] Updated openwisp-utils to 0.6.0
- [test] Added functions to add inline fields in extended app's integration testing

Version 0.3.0 [2020-08-14]
--------------------------

Features
~~~~~~~~

- [models] Added `swappable models and extensible classes <https://github.com/openwisp/openwisp-users#extend-openwisp-users>`_
- [admin] Added support for `organization owners <https://github.com/openwisp/openwisp-users#organization-owners>`_
- [admin] Added default owner to each organization
- [api] Added `ObtainTokenView REST API endpoint <https://github.com/openwisp/openwisp-users#obtain-authentication-token>`_ for bearer authentication
- [api] Added `OPENWISP_USERS_AUTH_API <https://github.com/openwisp/openwisp-users#openwisp-users-auth-api>`_ and `OPENWISP_USERS_AUTH_THROTTLE_RATE <https://github.com/openwisp/openwisp-users#openwisp-users-auth-throttle-rate>`_ settings
- [api] Added `Django REST Framework permission classes <https://github.com/openwisp/openwisp-users#django-rest-framework-permission-classes>`_
- [models] Added `Organization membership helpers <https://github.com/openwisp/openwisp-users#organization-membership-helpers>`_
- [models] Added `User permission helpers <https://github.com/openwisp/openwisp-users#permissions-helpers>`_

Changes
~~~~~~~

- Enabled `organization owner admin <https://github.com/openwisp/openwisp-users#openwisp-organization-owner-admin>`_ by default
- [dependencies] Upgraded ``django-allauth 0.42.0``, ``django-extensions 3.0.2``,
  ``openwisp-utils 0.5[rest]`` and ``phonenumbers 8.12.0``

Bugfixes
~~~~~~~~

- [admin] Fixed administrator edit/delete users of the same organization
- [admin] Fixed unique validation error on empty phone number

Version 0.2.2 [2020-05-04]
--------------------------

- [admin] Fixed regression that caused superusers to
  not be able to delete regular users
- [admin] Do not de-register socialaccount if not enabled

Version 0.2.1 [2020-04-07]
--------------------------

- [admin] Add possibility to deactivate users in batch operation
- [admin] Wrapped password forgot in row div
- [admin] Show latest items first in "recovery deleted <object>" pages

Version 0.2.0 [2020-01-17]
---------------------------

- [dependencies] Added support for django 3.0, dropped support for django < 2.1
- [python] Dropped support for python 2.7

Version 0.1.12 [2019-12-20]
---------------------------

- [dependencies] Added support for django 2.2

Version 0.1.11 [2019-12-13]
---------------------------

- [admin] Show ``is_staff`` and ``is_superuser`` in user list
- [admin] Allow adding organization in user creation form
- [admin] ``UserCreationForm`` encourages to select the organization
- [admin] Non-superusers now can manage the users of their organization
- [admin] Made ``OrganizationOwner`` and ``OrganizationUser`` admins multi-tenant
- [admin] Disabled ``OrganizationOwnerAdmin`` by default
- [admin] Disabled ``OrganizationUserAdmin`` by default
- [admin] Disabled ``view_on_site`` for ``OrganizationUserInline``
- [admin] Added menu items
- [admin] Avoid 500 error in case of SMTP error when adding a new user
- [urls] Added social login views URLs
- [mixins] Moved ``MultitenantAdminMixin`` from openwisp-utils to openwisp-users
- [models] Add possibility to validate inverse relations
- [model] Added phone_number field to User
- [models] Add unique constraint on user.email
- [models] Email: allow ``NULL`` but set ``UNIQUE`` constraint
- [models] Added ``_validate_org_reverse_relation``

Version 0.1.10 [2018-08-01]
---------------------------

- `#26 <https://github.com/openwisp/openwisp-users/pull/26>`_:
  [admin] Fixed Integrity error if trying to change email that exists
  (thanks to `@R9295 <https://github.com/R9295>`_)
- `#27 <https://github.com/openwisp/openwisp-users/issues/27>`_:
  [requirements] Added support for django 2.1 rc

Version 0.1.9 [2018-07-27]
--------------------------

- `#25 <https://github.com/openwisp/openwisp-users/pull/25>`_:
  [docs] Updated setup instructions in README
  (thanks to `@AlmogCohen <https://github.com/AlmogCohen>`_)
- `#20 <https://github.com/openwisp/openwisp-users/issues/20>`_:
  [tests] Fixed pending migration check
- [requirements] Updated dependencies

Version 0.1.8 [2018-02-19]
--------------------------

- fixed django 2.0 support and django-allauth to 0.35.0

Version 0.1.7 [2017-12-22]
--------------------------

- upgraded django to 2.0 and django-allauth to 0.34.0

Version 0.1.6 [2017-12-02]
--------------------------

- `c5b648e <https://github.com/openwisp/openwisp-users/commit/c5b648e>`_:
  [mixins] Extracted logic of ``OrgMixin`` to ``ValidateOrgMixin``

Version 0.1.5 [2017-08-29]
--------------------------

- `#3 <https://github.com/openwisp/openwisp-users/issues/3>`_:
  [admin] Allow operators to manage users without being
  able to change superuser related details
- `31b13bb <https://github.com/openwisp/openwisp-users/commit/31b13bb>`_:
  [requirements] Updated django-allauth to 0.33.0

Version 0.1.4 [2017-05-15]
--------------------------

- `f49f900 <https://github.com/openwisp/openwisp-users/commit/f49f900>`_:
  [admin] Removed view on site link in organization admin
- `2144b29 <https://github.com/openwisp/openwisp-users/commit/2144b29>`_:
  [admin] Removed view on site link in organization user admin
- `dcef200 <https://github.com/openwisp/openwisp-users/commit/dcef200>`_:
  [requirements] Updated django-allauth to 0.32.0

Version 0.1.3 [2017-03-15]
--------------------------

- `f9056e9 <https://github.com/openwisp/openwisp-users/commit/f9056e9>`_:
  [admin] Always require email
- `c21c782 <https://github.com/openwisp/openwisp-users/commit/c21c782>`_:
  [mixins] Fixed bugged org pk comparison in ``_validate_org_relation``
- `763c261 <https://github.com/openwisp/openwisp-users/commit/763c261>`_:
  [accounts] Added back frontend logout url
- `b93de81 <https://github.com/openwisp/openwisp-users/commit/b93de81>`_:
  [admin] Added back site model

Version 0.1.2 [2017-03-10]
--------------------------

- `b615f4c <https://github.com/openwisp/openwisp-users/commit/b615f4c>`_:
  [admin] Unregister ``allauth.socialaccount`` models
- `d6a2294 <https://github.com/openwisp/openwisp-users/commit/d6a2294>`_:
  [allauth] Added proxy URLs for ``allauth.acounts``

Version 0.1.1 [2017-03-07]
--------------------------

- [mixins] Fixed relation name in `OrgMixin` and `ShareableOrgMixin`

Version 0.1.0 [2017-03-06]
--------------------------

- added basic multi-tenancy features for OpenWISP 2
