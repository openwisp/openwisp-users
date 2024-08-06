Developer Installation Instructions
===================================

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of contents**:
    :depth: 2
    :local:

Installing for Development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev openssl libssl-dev

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-users
    cd openwisp-users/
    pip install -e .[rest]

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

Run celery and celery-beat with the following commands (separate terminal
windows are needed):

.. code-block:: shell

    cd tests/
    celery -A openwisp2 worker -l info
    celery -A openwisp2 beat -l info

Launch development server:

.. code-block:: shell

    ./manage.py runserver

You can access the admin interface at ``http://127.0.0.1:8000/admin/``.

Run tests with:

.. code-block:: shell

    # --parallel and --keepdb are optional but help to speed up the operation
    ./runtests.py --parallel --keepdb

Alternative Sources
-------------------

Pypi
~~~~

To install the latest Pypi:

.. code-block:: shell

    pip install openwisp-users

Github
~~~~~~

To install the latest development version tarball via HTTPs:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-users/tarball/master

Alternatively you can use the git protocol:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-users#egg=openwisp_users
