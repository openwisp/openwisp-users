Install stable version from pypi
================================

.. include:: ../partials/developer-docs.rst

Install from pypi:

.. code-block:: shell

    pip install openwisp-users

Install development version
===========================

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-users/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-users#egg=openwisp_users

Installing for development
==========================

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

Run celery and celery-beat with the following commands (separate terminal windows are
needed):

.. code-block:: shell

    cd tests/
    celery -A openwisp2 worker -l info
    celery -A openwisp2 beat -l info

Launch development server:

.. code-block:: shell

    ./manage.py runserver

You can access the admin interface at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    # --parallel and --keepdb are optional but help to speed up the operation
    ./runtests.py --parallel --keepdb
