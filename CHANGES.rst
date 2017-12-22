Changelog
=========

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
