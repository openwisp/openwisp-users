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

------------

Provides basic multi-tenancy features for OpenWISP 2 (using the Django web-framework).

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

If you want to contribute, install your cloned fork:

.. code-block:: shell

    git clone git@github.com:<your_fork>/openwisp-users.git
    cd openwisp-users
    python setup.py develop

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
        'django.contrib.admin',
        'django.contrib.sites',
        'django_extensions',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'openwisp_users',
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
    ]

    urlpatterns += staticfiles_urlpatterns()


For additional steps to properly configure ``allauth`` in your project, please refer to their documentation: `allauth documentation installation section <http://django-allauth.readthedocs.io/en/latest/installation.html>`_.

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

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

Set ``EMAIL_PORT`` in ``settings.py`` to a port number (eg: ``1025``):

.. code-block:: python

    EMAIL_PORT = '1025'

Launch development server and SMTP debugging server:

.. code-block:: shell

    ./manage.py runserver
    # open another terminal and run
    python -m smtpd -n -c DebuggingServer localhost:1025

You can access the admin interface at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py

Settings
--------

``OPENWISP_ORGANIZATON_USER_ADMIN``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``boolean``      |
+--------------+------------------+
| **default**: | ``False``        |
+--------------+------------------+

Indicates whether the admin section for managing ``OrganizationUser`` items
is enabled or not.

It is disabled by default because these items can be managed via inline items
in the user administration section.

``OPENWISP_ORGANIZATON_OWNER_ADMIN``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+------------------+
| **type**:    | ``boolean``      |
+--------------+------------------+
| **default**: | ``False``        |
+--------------+------------------+

Indicates whether the admin section for managing ``OrganizationOwner`` items
is enabled or not.

It is disabled by default because `OpenWISP <http://openwisp.org>`_ does not use
this feature of `django-organizations <https://github.com/bennylope/django-organizations>`_ yet.

Multitenancy mixins
-------------------

* **MultitenantAdminMixin**: adding this mixin to a ``ModelAdmin`` class will make it multitenant.
  Set ``multitenant_shared_relations`` to the list of parameters you wish to have only organization
  specific options.

* **MultitenantOrgFilter**: admin filter that shows only organizations the current user is associated with in its available choices.

* **MultitenantRelatedOrgFilter**: similar ``MultitenantOrgFilter`` but shows only objects which have a relation with
  one of the organizations the current user is associated with.

Contributing
------------

1. Announce your intentions in the `OpenWISP Mailing List <https://groups.google.com/d/forum/openwisp>`_
2. Fork this repo and install it
3. Follow `PEP8, Style Guide for Python Code`_
4. Write code
5. Write tests for your code
6. Ensure all tests pass
7. Ensure test coverage does not decrease
8. Document your changes
9. Send pull request

.. _PEP8, Style Guide for Python Code: http://www.python.org/dev/peps/pep-0008/

Changelog
---------

See `CHANGES <https://github.com/openwisp/openwisp-users/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE <https://github.com/openwisp/openwisp-users/blob/master/LICENSE>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.
