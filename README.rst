openwisp-users
==============

.. image:: https://travis-ci.org/openwisp/openwisp-users.svg
   :target: https://travis-ci.org/openwisp/openwisp-users

.. image:: https://coveralls.io/repos/openwisp/openwisp-users/badge.svg
  :target: https://coveralls.io/r/openwisp/openwisp-users

.. image:: https://requires.io/github/openwisp/openwisp-users/requirements.svg?branch=master
   :target: https://requires.io/github/openwisp/openwisp-users/requirements/?branch=master
   :alt: Requirements Status

.. image:: https://badge.fury.io/py/openwisp-users.svg
   :target: http://badge.fury.io/py/openwisp-users

.. image:: https://pepy.tech/badge/openwisp-users
   :target: https://pepy.tech/project/openwisp-users
   :alt: downloads

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://pypi.org/project/black/
   :alt: code style: black

------------

Implementation of user management and multi-tenancy for OpenWISP (built with python & django).

.. image:: https://raw.githubusercontent.com/openwisp/openwisp2-docs/master/assets/design/openwisp-logo-black.svg
  :target: http://openwisp.org

------------

.. contents:: **Table of Contents**:
   :backlinks: none
   :depth: 3

------------

Deploy it in production
-----------------------

An automated installer is available at `ansible-openwisp2 <https://github.com/openwisp/ansible-openwisp2>`_.

Install stable version from pypi
--------------------------------

Install from pypi:

.. code-block:: shell

    pip install openwisp-users

Install development version
---------------------------

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-users/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-users#egg=openwisp_users


Setup (integrate in an existing django project)
-----------------------------------------------

``INSTALLED_APPS`` in ``settings.py`` should look like the following:

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'openwisp_utils.admin_theme',
        # overrides some templates in django-allauth
        'openwisp_users.accounts',
        'django_extensions',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        # must come before the django admin
        # to override the admin login page
        'openwisp_users',
        'django.contrib.admin',
        'django.contrib.sites',
        'rest_framework',
        'rest_framework.authtoken',
        'drf_yasg',
    ]

also add ``AUTH_USER_MODEL`` and ``SITE_ID`` to your ``settings.py``::

    AUTH_USER_MODEL = 'openwisp_users.User'
    SITE_ID = 1

``urls.py``:

.. code-block:: python

    from django.conf.urls import include, url
    from django.contrib import admin
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
        url(r'^accounts/', include('allauth.urls')),
        url(r'^api/v1/', include('openwisp_users.api.urls')),
    ]

    urlpatterns += staticfiles_urlpatterns()


For additional steps to properly configure ``allauth`` in your project,
please refer to their documentation:
`allauth documentation installation section <http://django-allauth.readthedocs.io/en/latest/installation.html>`_.

Installing for development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev openssl libssl-dev

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-users
    cd openwisp-users/
    python setup.py develop

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Start Redis

.. code-block:: shell

    docker-compose up -d

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

Launch development server:

.. code-block:: shell

    ./manage.py runserver

You can access the admin interface at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    # --parallel and --keepdb are optional but help to speed up the operation
    ./runtests.py --parallel --keepdb

Settings
--------

``OPENWISP_ORGANIZATION_USER_ADMIN``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``boolean``      |
+--------------+------------------+
| **default**: | ``False``        |
+--------------+------------------+

Indicates whether the admin section for managing ``OrganizationUser`` items
is enabled or not.

It is disabled by default because these items can be managed via inline items
in the user administration section.

``OPENWISP_ORGANIZATION_OWNER_ADMIN``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``boolean``      |
+--------------+------------------+
| **default**: | ``True``         |
+--------------+------------------+

Indicates whether the admin section for managing ``OrganizationOwner`` items
is enabled or not.

Find out more information about `organization owners <#organization-owners>`_.

``OPENWISP_USERS_AUTH_API``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+--------------+
| **type**:    | ``boolean``  |
+--------------+--------------+
| **default**: | ``False``    |
+--------------+--------------+

Indicates whether the `REST API <#rest-api>`_ is enabled or not.

``OPENWISP_USERS_AUTH_THROTTLE_RATE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+--------------+
| **type**:    | ``str``      |
+--------------+--------------+
| **default**: | ``100/day``  |
+--------------+--------------+

Indicates the rate throttling for the
`Obtain Authentication <#obtain-authentication-token>`_ API endpoint.

Please note that the current rate throttler is very basic and will
also count valid requests for rate limiting. For more information,
check Django-rest-framework
`throttling guide <https://www.django-rest-framework.org/api-guide/throttling/>`_.

REST API
--------

To enable the API the setting
`OPENWISP_USERS_AUTH_API <#openwisp-users-auth-api>`_
must be set to ``True``.

Live documentation
~~~~~~~~~~~~~~~~~~

A general live API documentation (following the OpenAPI specification) at ``/api/v1/docs/``.

Browsable web interface
~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://github.com/openwisp/openwisp-users/raw/master/docs/images/api-ui.png

Additionally, opening any of the endpoints listed below
directly in the browser will show the `browsable API interface of Django-REST-Framework
<https://www.django-rest-framework.org/topics/browsable-api/>`_,
which makes it even easier to find out the details of each endpoint.

Obtain Authentication Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    /api/v1/user/token/

This endpoint only accepts the ``POST`` method and is used to retrieve the
Bearer token that is required to make API requests to other endpoints.

Example usage of the endpoint:

.. code-block:: shell

    http POST localhost:8000/api/v1/user/token/ username=openwisp password=1234

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

Authenticating with the user token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The authentication class ``openwisp_users.api.authentication.BearerAuthentication``
is used across the different OpenWISP modules for authentication.

To use it, first of all get the user token as described above in
`Obtain Authentication Token <#obtain-authentication-token>`_, then send
the token in the ``Authorization`` header:

.. code-block:: shell

    # get token
    TOKEN=$(http POST :8000/api/v1/user/token/ username=openwisp password=1234 | jq -r .token)

    # send bearer token
    http GET localhost:8000/api/v1/firmware/build/ "Authorization: Bearer $TOKEN"

Organization permissions
------------------------

Here's a summary of the default permissions:

- All users who belong to the Administrators group and are organization
  managers (``OrganizationUser.is_admin=True``), have the permission to edit
  the organizations details which they administrate.
- Only super users have the permission to add and delete organizations.
- Only super users and `organization owners <#organization-owners>`_
  have the permission to change the ``OrganizationOwner`` inline or delete the relation.

Organization Owners
-------------------

An organization owner is a user who is designated as the owner
of a particular organization and this owner can not be deleted
or edited by other administrators. Only the superuser has the permissions to do this.

By default, the first manager of an organization is designated as the owner of that organization.

If the ``OrganizationUser`` instance related to the owner of an organization is deleted
or flagged as ``is_admin=False``, the admin interface will return an error informing
users that the operation is not allowed, the owner should be changed before attempting to do that.

Organization membership helpers
-------------------------------

The ``User`` model provides methods to check whether the user
is a member, manager or owner of an organization in an efficient way.

These methods are needed because an user may be administrator in one organization,
but simple end-user is another organization, so we need to easily distinguish
between the different use cases and at the same time avoid to generate too
many database queries.

.. code-block:: python

    import swapper

    User = swapper.load_model('openwisp_users', 'User')
    Organization = swapper.load_model('openwisp_users', 'Organization')

    user = User.objects.first()
    org = Organization.objects.first()
    user.is_member(org)
    user.is_manager(org)
    user.is_owner(org)

    # also valid (avoids query to retrieve Organization instance)
    device = Device.objects.first()
    user.is_member(device.organization_id)
    user.is_manager(device.organization_id)
    user.is_owner(device.organization_id)

``is_member(org)``
~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance passed.
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

This check shall be used when access needs to be granted to end-users who
need to consume a service offered by an organization they're member of
(eg: authenticate to a public wifi service).

``is_manager(org)``
~~~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance
and has the ``OrganizationUser.is_admin`` field set to ``True``.
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

This check shall be used when access needs to be granted to the managers of
an organization users who need to perform administrative tasks
(eg: download the firmware image of their organization).

``is_owner(org)``
~~~~~~~~~~~~~~~~~

Returns ``True`` if the user is member of the ``Organization`` instance
and is owner of the organization (checks the presence of an
``OrganizationOwner`` instance for the user).
Alternatively, ``UUID`` or ``str`` can be passed instead of an organization instance,
which will be interpreted as the organization primary key; this second option is
recommended when building the organization instance requires an extra query.

There can be only one owner for each organization.

This check shall be used to avoid that managers would be able to take control
of an organization and exclude the original owner without their consent.

``organizations_dict``
~~~~~~~~~~~~~~~~~~~~~~

The methods described above use the ``organizations_dict`` property method under
the hood, which builds a dictionary in which each key contains the primary key
of the organization the user is member of, and each key contains another dictionary
which allows to easily determine if the user is manager (``is_admin``) and owner
(``is_owner``).

**This data structure is cached automatically and accessing it multiple times
over the span of multiple requests will not generate multiple database queries.**

The cache invalidation also happens automatically whenever an ``OrganizationUser``
or an ``OrganizationOwner`` instance is added, changed or deleted.

Usage exmaple:

.. code-block:: python

    >>> user.organizations_dict
    ... {'20135c30-d486-4d68-993f-322b8acb51c4': {'is_admin': True, 'is_owner': False}}
    >>> user.organizations_dict.keys()
    ... dict_keys(['20135c30-d486-4d68-993f-322b8acb51c4'])

``organizations_managed``
~~~~~~~~~~~~~~~~~~~~~~~~~

This attribute returns a list containing the primary keys of the organizations
which the user can manage.

Usage example:

.. code-block:: python

    >>> user.organizations_managed
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

``organizations_owned``
~~~~~~~~~~~~~~~~~~~~~~~

This attribute returns a list containing the primary keys of the organizations
which the user owns.

Usage example:

.. code-block:: python

    >>> user.organizations_owned
    ... ['20135c30-d486-4d68-993f-322b8acb51c4']

Permissions helpers
-------------------

The ``User`` model provides methods to check permissions in an efficient way
(without generating database queries each time the permissions are accessed).

``permissions``
~~~~~~~~~~~~~~~

The ``permissions`` property helper returns the user's permissions
from the cache, cache invalidation is handled automatically.

.. code-block:: python

    >>> user.permissions
    ... {'account.add_emailaddress',
         'account.change_emailaddress',
         'account.delete_emailaddress',
         'account.view_emailaddress',
         'openwisp_users.add_organizationuser',
         'openwisp_users.add_user',
         'openwisp_users.change_organizationuser',
         'openwisp_users.change_user',
         'openwisp_users.delete_organizationuser',
         'openwisp_users.delete_user'}

``has_permission(permission)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For superusers, the method returns ``True`` regardless of the permission passed to it.
While for other users, the method checks whether the user has the specified permission and
returns ``True`` or ``False`` accordingly.

It uses the `permissions property helper <#permissions>`_ under the hood
to avoid generating database queries each time is called.

.. code-block:: python

    >>> user.has_permission('openwisp_users.add_user')
    ... True

Django REST Framework Permission Classes
----------------------------------------

The custom `Django REST Framework <https://www.django-rest-framework.org/>`_
permission classes ``IsOrganizationMember``, ``IsOrganizationManager``
and ``IsOrganizationOwner`` can be used in the API to ensure that the
request user is in the same organization as requested object and is
organization member, manager or owner respectively. Usage example:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics

    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationMember,)

``organization_field``
~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``string``       |
+--------------+------------------+
| **default**: | ``organization`` |
+--------------+------------------+

``organization_field`` can be used to define where to look to
find the organization of the current object.
In most cases this won't need to be changed, but it does need to
be changed when the ``organization`` is defined only on a parent object.

For example, in `openwisp-firmware-upgrader <https://github.com/openwisp/openwisp-firmware-upgrader>`_,
``organization`` is defined on ``Category`` and ``Build`` has a relation
to ``category``, so the organization of Build instances is inferred from
the organization of the Category.

Therefore, to implement the permission class correctly, we would have to do:

.. code-block:: python

    from openwisp_users.api.permissions import IsOrganizationManager
    from rest_framework import generics

    class MyApiView(generics.APIView):
        permission_classes = (IsOrganizationMember,)
        organization_field = 'category__organization'

This will translate into accessing ``obj.category.organization``.
Ensure the queryset of your views make use of
`select_related <https://docs.djangoproject.com/en/3.0/ref/models/querysets/#select-related>`_
in these cases to avoid generating too many queries.

Multitenancy mixins
-------------------

* **MultitenantAdminMixin**: adding this mixin to a ``ModelAdmin`` class will make it multitenant
  (users will only be able to see items of the organizations they manage or own).
  Set ``multitenant_shared_relations`` to the list of parameters you wish to have only organization
  specific options.

* **MultitenantOrgFilter**: admin filter that shows only organizations the current user can manage in its available choices.

* **MultitenantRelatedOrgFilter**: similar ``MultitenantOrgFilter`` but shows only objects which have a relation with
  one of the organizations the current user can manage.

Extend openwisp-users
---------------------

One of the core values of the OpenWISP project is `Software Reusability <http://openwisp.io/docs/general/values.html#software-reusability-means-long-term-sustainability>`_,
for this reason *openwisp-users* provides a set of base classes
which can be imported, extended and reused to create derivative apps.

This will be extreme beneficial for you if you want to create additional
fields for User model, example asking for Social Security Number of the
User for registeration.

In order to implement your custom version of *openwisp-users*,
you need to perform the steps described in this section.

When in doubt, the code in the `test project <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/>`_ and
the `sample app <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/>`_
will serve you as source of truth:
just replicate and adapt that code to get a basic derivative of
*openwisp-users* working.

**Premise**: if you plan on using a customized version of this module,
we suggest to start with it since the beginning, because migrating your data
from the default module to your extended version may be time consuming.

1. Initialize your custom module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first thing you need to do is to create a new django app which will
contain your custom version of *openwisp-users*.

A django app is nothing more than a
`python package <https://docs.python.org/3/tutorial/modules.html#packages>`_
(a directory of python scripts), in the following examples we'll call this django app
``myusers``, but you can name it how you want::

    django-admin startapp myusers

Keep in mind that the command mentioned above must be called from a directory
which is available in your `PYTHON_PATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_
so that you can then import the result into your project.

Now you need to add ``myusers`` to ``INSTALLED_APPS`` in your ``settings.py``,
ensuring also that ``openwisp_users`` has been removed:

.. code-block:: python

    INSTALLED_APPS = [
        # ... other apps ...

        # 'openwisp_users'  <-- comment out or delete this line
        'myusers'
    ]

For more information about how to work with django projects and django apps, please refer
to the `django documentation <https://docs.djangoproject.com/en/dev/intro/tutorial01/>`_.

2. Install ``openwisp-users``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install (and add to the requirement of your project) openwisp-users::

    pip install openwisp-users

3. Add ``EXTENDED_APPS``
~~~~~~~~~~~~~~~~~~~~~~~~

Add the following to your ``settings.py``:

.. code-block:: python

    EXTENDED_APPS = ('openwisp_users',)


4. Add ``openwisp_utils.staticfiles.DependencyFinder``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.staticfiles.DependencyFinder`` to
``STATICFILES_FINDERS`` in your ``settings.py``:

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'openwisp_utils.staticfiles.DependencyFinder',
    ]

5. Add ``openwisp_utils.loaders.DependencyLoader``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.loaders.DependencyLoader`` to ``TEMPLATES`` in your ``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    'openwisp_utils.loaders.DependencyLoader',
                ],
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        }
    ]

6. Inherit the AppConfig class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please refer to the following files in the sample app of the test project:

- `openwisp_users/__init__.py <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/__init__.py>`_
- `openwisp_users/apps.py <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/apps.py>`_

You have to replicate and adapt that code in your project.

For more information regarding the concept of ``AppConfig`` please refer to
the `"Applications" section in the django documentation <https://docs.djangoproject.com/en/dev/ref/applications/>`_.

7. Create your custom models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the purpose of showing an example, we added a simple ``social_security_number`` field in User model to the
`models of the sample app in the test project <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/models.py>`_.

You can add fields in a similar way in your ``models.py`` file.

For doubts regarding how to use, extend or develop models please refer to the
`"Models" section in the django documentation <https://docs.djangoproject.com/en/dev/topics/db/models/>`_.

8. Add swapper configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have created the models, add the following to your ``settings.py``:

.. code-block:: python

    # Setting models for swapper module
    AUTH_USER_MODEL = 'myusers.User'
    OPENWISP_USERS_GROUP_MODEL = 'myusers.Group'
    OPENWISP_USERS_ORGANIZATION_MODEL = 'myusers.Organization'
    OPENWISP_USERS_ORGANIZATIONUSER_MODEL = 'myusers.OrganizationUser'
    OPENWISP_USERS_ORGANIZATIONOWNER_MODEL = 'myusers.OrganizationOwner'

Substitute ``myusers`` with the name you chose in step 1.

9. Create database migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create database migrations::

    ./manage.py makemigrations

Now, manually create a file ``0002_default_groups_and_permissions.py`` in the migrations directory just create by the ``makemigrations`` command and copy contents of the `sample_users/migrations/0002_default_groups_and_permissions.py <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/migrations/0002_default_groups_and_permissions.py>`_.

Apply database migrations::

    ./manage.py migrate

10. Create the admin
~~~~~~~~~~~~~~~~~~~~

Refer to the `admin.py file of the sample app <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/admin.py>`_.

To introduce changes to the admin, you can do it in two main ways which are described below.

For more information regarding how the django admin works, or how it can be customized, please refer to
`"The django admin site" section in the django documentation <https://docs.djangoproject.com/en/dev/ref/contrib/admin/>`_.

1. Monkey patching
^^^^^^^^^^^^^^^^^^

If the changes you need to add are relatively small, you can resort to monkey patching.

For example:

.. code-block:: python

    from openwisp_users.admin import (
        UserAdmin,
        GroupAdmin,
        OrganizationAdmin,
        OrganizationOwnerAdmin,
        BaseOrganizationUserAdmin,
    )

    # OrganizationAdmin.field += ['example_field'] <-- Monkey patching changes example

For your convenience of adding fields in User forms, we provide the following functions:

usermodel_add_form
""""""""""""""""""

When monkey patching the ``UserAdmin`` class to add add fields in the
"Add user" form, you can use this function. In the example, `Social Security Number is added in the add form <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/master/docs/images/add_user.png
   :alt: Social Security Number in Add form

usermodel_change_form
"""""""""""""""""""""

When monkey patching the ``UserAdmin`` class to add fields in the
"Change user" form to change / modify user form's profile section,
you can use this function. In the example, `Social Security Number
is added in the change form <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/master/docs/images/change_user.png
   :alt: Social Security Number in Change form

usermodel_list_and_search
"""""""""""""""""""""""""

When monkey patching the ``UserAdmin`` class you can use this
function to make field searchable and add it to the user
display list view. In the example, `Social Security Number is added in the changelist view <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/master/docs/images/search_user.png
   :alt: Users Change List View

2. Inheriting admin classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to introduce significant changes and/or you don't want to resort to
monkey patching, you can proceed as follows:

.. code-block:: python

    from django.contrib import admin
    from openwisp_users.admin import (
        UserAdmin as BaseUserAdmin,
        GroupAdmin as BaseGroupAdmin,
        OrganizationAdmin as BaseOrganizationAdmin,
        OrganizationOwnerAdmin as BaseOrganizationOwnerAdmin,
        OrganizationUserAdmin as BaseOrganizationUserAdmin,
    )
    from swapper import load_model
    from django.contrib.auth import get_user_model

    Group = load_model('openwisp_users', 'Group')
    Organization = load_model('openwisp_users', 'Organization')
    OrganizationOwner = load_model('openwisp_users', 'OrganizationOwner')
    OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
    User = get_user_model()

    admin.site.unregister(Group)
    admin.site.unregister(Organization)
    admin.site.unregister(OrganizationOwner)
    admin.site.unregister(OrganizationUser)
    admin.site.unregister(User)


    @admin.register(Group)
    class GroupAdmin(BaseGroupAdmin):
        pass


    @admin.register(Organization)
    class OrganizationAdmin(BaseOrganizationAdmin):
        pass


    @admin.register(OrganizationOwner)
    class OrganizationOwnerAdmin(BaseOrganizationOwnerAdmin):
        pass


    @admin.register(OrganizationUser)
    class OrganizationUserAdmin(BaseOrganizationUserAdmin):
        pass


    @admin.register(User)
    class UserAdmin(BaseUserAdmin):
        pass

11. Create root URL configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please refer to the `urls.py <https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/urls.py>`_ file in the sample project.

For more information about URL configuration in django, please refer to the
`"URL dispatcher" section in the django documentation <https://docs.djangoproject.com/en/dev/topics/http/urls/>`_.

12. Import the automated tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When developing a custom application based on this module, it's a good
idea to import and run the base tests too, so that you can be sure the changes
you're introducing are not breaking some of the existing features of *openwisp-users*.

In case you need to add breaking changes, you can overwrite the tests defined
in the base classes to test your own behavior.

See the `tests of the sample app <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/tests.py>`_
to find out how to do this.

You can then run tests with::

    # the --parallel flag is optional
    ./manage.py test --parallel myusers

Substitute ``myusers`` with the name you chose in step 1.

Other base classes that can be inherited and extended
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following steps are not required and are intended for more advanced customization.

1. Extending the API Views
^^^^^^^^^^^^^^^^^^^^^^^^^^

The API view classes can be extended into other django applications as well. Note
that it is not required for extending *openwisp-users* to your app and this change
is required only if you plan to make changes to the API views.

Create a view file as done in `API views.py <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/views.py>`_.

Remember to use these views in root URL configurations in point 11.

For more information about django views, please refer to the
`views section in the django documentation <https://docs.djangoproject.com/en/dev/topics/http/views/>`_.

Contributing
------------

Please refer to the `OpenWISP contributing guidelines <http://openwisp.io/docs/developer/contributing.html>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.

Changelog
---------

See `CHANGES <https://github.com/openwisp/openwisp-users/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE <https://github.com/openwisp/openwisp-users/blob/master/LICENSE>`_.
