#!/bin/bash
# Install the host and Python dependencies for the selected CI row.
set -e

if [ "${CI_SYSTEM_DEPS_READY:-0}" != 1 ]; then
    sudo apt update -qq
    sudo apt-get -qq -y install gettext
    sudo npm install -g prettier
fi
if [ "${CI_SYSTEM_DEPS_ONLY:-0}" = 1 ]; then
    exit 0
fi

python -m pip install -U pip wheel setuptools
python -m pip install -U -r requirements-test.txt
python -m pip install -e '.[rest]'
python -m pip install -U "${DJANGO_VERSION:?Set DJANGO_VERSION to a CI matrix value}"
