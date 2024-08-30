Extending OpenWISP Users
========================

.. include:: ../partials/developer-docs.rst

One of the core values of the OpenWISP project is :ref:`Software
Reusability <values_software_reusability>`, which ensures long-term
sustainability. For this reason, *OpenWISP Users* provides a set of base
classes that can be imported, extended, and reused to create derivative
apps.

This is extremely beneficial if you want to add additional fields to the
User model, such as requesting a Social Security Number during
registration.

To implement your custom version of *OpenWISP Users*, follow the steps
described in this section.

If you have any doubts, refer to the code in the `test project
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/>`_
and the `sample app
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/>`_.
These resources will serve as your source of truth: replicate and adapt
that code to get a basic derivative of *OpenWISP Users* working.

.. important::

    If you plan on using a customized version of this module, we suggest
    to start with it since the beginning, because migrating your data from
    the default module to your extended version may be time consuming.

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

1. Initialize Your Custom Module
--------------------------------

The first thing you need to do is create a new Django app which will
contain your custom version of *OpenWISP Users*.

A Django app is nothing more than a `Python package
<https://docs.python.org/3/tutorial/modules.html#packages>`_ (a directory
of Python scripts). In the following examples, we'll call this Django app
``myusers``, but you can name it however you like:

.. code-block::

    django-admin startapp myusers

Keep in mind that the command mentioned above must be called from a
directory that is available in your `PYTHON_PATH
<https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_ so that
you can then import the result into your project.

Now you need to add ``myusers`` to ``INSTALLED_APPS`` in your
``settings.py``, ensuring also that ``openwisp_users`` has been removed:

.. code-block:: python

    INSTALLED_APPS = [
        # ... other apps ...
        # 'openwisp_users'  <-- comment out or delete this line
        "myusers"
    ]

For more information about how to work with Django projects and Django
apps, please refer to the `Django documentation
<https://docs.djangoproject.com/en/4.2/intro/tutorial01/>`_.

2. Install OpenWISP Users
-------------------------

Install (and add to the requirements of your project) openwisp-users:

.. code-block::

    pip install openwisp-users

3. Add ``EXTENDED_APPS``
------------------------

Add the following to your ``settings.py``:

.. code-block:: python

    EXTENDED_APPS = ("openwisp_users",)

4. Add ``openwisp_utils.staticfiles.DependencyFinder``
------------------------------------------------------

Add ``openwisp_utils.staticfiles.DependencyFinder`` to
``STATICFILES_FINDERS`` in your ``settings.py``:

.. code-block:: python

    STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "openwisp_utils.staticfiles.DependencyFinder",
    ]

5. Add ``openwisp_utils.loaders.DependencyLoader``
--------------------------------------------------

Add ``openwisp_utils.loaders.DependencyLoader`` to ``TEMPLATES`` before
``django.template.loaders.app_directories.Loader`` in your
``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "loaders": [
                    "django.template.loaders.filesystem.Loader",
                    "openwisp_utils.loaders.DependencyLoader",
                    "django.template.loaders.app_directories.Loader",
                ],
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        }
    ]

6. Inherit the AppConfig Class
------------------------------

Please refer to the following files in the sample app of the test project:

- `openwisp_users/__init__.py
  <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/__init__.py>`_
- `openwisp_users/apps.py
  <https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/apps.py>`_

You have to replicate and adapt that code in your project.

For more information regarding the concept of ``AppConfig`` please refer
to the `"Applications" section in the django documentation
<https://docs.djangoproject.com/en/4.2/ref/applications/>`_.

7. Create Your Custom Models
----------------------------

For the purpose of showing an example, we added a simple
``social_security_number`` field in the User model to the `models of the
sample app in the test project
<https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/models.py>`_.

You can add fields in a similar way in your ``models.py`` file.

For doubts regarding how to use, extend, or develop models please refer to
the `"Models" section in the django documentation
<https://docs.djangoproject.com/en/4.2/topics/db/models/>`_.

8. Add Swapper Configurations
-----------------------------

Once you have created the models, add the following to your
``settings.py``:

.. code-block:: python

    # Setting models for swapper module
    AUTH_USER_MODEL = "myusers.User"
    OPENWISP_USERS_GROUP_MODEL = "myusers.Group"
    OPENWISP_USERS_ORGANIZATION_MODEL = "myusers.Organization"
    OPENWISP_USERS_ORGANIZATIONUSER_MODEL = "myusers.OrganizationUser"
    OPENWISP_USERS_ORGANIZATIONOWNER_MODEL = "myusers.OrganizationOwner"
    # The following model is not used in OpenWISP yet
    # but users are free to implement it in their projects if needed
    # for more information refer to the django-organizations docs:
    # https://django-organizations.readthedocs.io/
    OPENWISP_USERS_ORGANIZATIONINVITATION_MODEL = (
        "myusers.OrganizationInvitation"
    )

Substitute ``myusers`` with the name you chose in step 1.

9. Create Database Migrations
-----------------------------

Create database migrations:

.. code-block::

    ./manage.py makemigrations

Now, manually create a file ``0004_default_groups.py`` in the migrations
directory just created by the ``makemigrations`` command and copy the
contents of the `sample_users/migrations/0004_default_groups.py
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/migrations/0004_default_groups.py>`_.

Then, run the migrations:

.. code-block::

    ./manage.py migrate

.. note::

    The ``0004_default_groups`` is required because other OpenWISP modules
    depend on it. If it's not created as documented here, the migrations
    of other OpenWISP modules will fail.

10. Create the admin
--------------------

Refer to the `admin.py file of the sample app
<https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/admin.py>`_.

To introduce changes to the admin, you can do it in two main ways which
are described below.

For more information regarding how the Django admin works, or how it can
be customized, please refer to `"The Django admin site" section in the
Django documentation
<https://docs.djangoproject.com/en/4.2/ref/contrib/admin/>`_.

1. Monkey Patching
~~~~~~~~~~~~~~~~~~

If the changes you need to add are relatively small, you can resort to
monkey patching.

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

For your convenience in adding fields in User forms, we provide the
following functions:

``usermodel_add_form``
++++++++++++++++++++++

When monkey patching the ``UserAdmin`` class to add fields in the "Add
user" form, you can use this function. In the example, `Social Security
Number is added in the add form
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/add_user.png
    :alt: Social Security Number in Add form

``usermodel_change_form``
+++++++++++++++++++++++++

When monkey patching the ``UserAdmin`` class to add fields in the "Change
user" form to change/modify the user form's profile section, you can use
this function. In the example, `Social Security Number is added in the
change form
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/change_user.png
    :alt: Social Security Number in Change form

``usermodel_list_and_search``
+++++++++++++++++++++++++++++

When monkey patching the ``UserAdmin`` class, you can use this function to
make a field searchable and add it to the user display list view. In the
example, `Social Security Number is added in the changelist view
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/sample_users/admin.py>`_:

.. image:: https://github.com/openwisp/openwisp-users/raw/docs/docs/images/search_user.png
    :alt: Users Change List View

2. Inheriting Admin Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need to introduce significant changes and/or you don't want to
resort to monkey patching, you can proceed as follows:

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

    Group = load_model("openwisp_users", "Group")
    Organization = load_model("openwisp_users", "Organization")
    OrganizationOwner = load_model("openwisp_users", "OrganizationOwner")
    OrganizationUser = load_model("openwisp_users", "OrganizationUser")
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

11. Create Root URL Configuration
---------------------------------

Please refer to the `urls.py
<https://github.com/openwisp/openwisp-users/tree/master/tests/openwisp2/urls.py>`_
file in the sample project.

For more information about URL configuration in Django, please refer to
the `"URL dispatcher" section in the Django documentation
<https://docs.djangoproject.com/en/4.2/topics/http/urls/>`_.

12. Import the Automated Tests
------------------------------

When developing a custom application based on this module, it's a good
idea to import and run the base tests too, so that you can be sure the
changes you're introducing are not breaking some of the existing features
of *OpenWISP Users*.

In case you need to add breaking changes, you can overwrite the tests
defined in the base classes to test your own behavior.

See the `tests of the sample app
<https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/tests.py>`_
to find out how to do this.

You can then run tests with:

.. code-block::

    # the --parallel flag is optional
    ./manage.py test --parallel myusers

Substitute ``myusers`` with the name you chose in step 1.

Other Base Classes that can be Inherited and Extended
-----------------------------------------------------

The following steps are not required and are intended for more advanced
customization.

Extending the API Views
~~~~~~~~~~~~~~~~~~~~~~~

The API view classes can be extended into other Django applications as
well. Note that it is not required for extending *OpenWISP Users* to your
app and this change is required only if you plan to make changes to the
API views.

Create a view file as done in `API views.py
<https://github.com/openwisp/openwisp-users/blob/master/tests/openwisp2/sample_users/views.py>`_.

Remember to use these views in root URL configurations in point 11.

For more information about Django views, please refer to the `views
section in the Django documentation
<https://docs.djangoproject.com/en/4.2/topics/http/views/>`_.
