Changelog
=========

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
