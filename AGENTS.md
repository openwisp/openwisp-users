# AGENTS.md

## Project Overview

`openwisp-users` is the OpenWISP Django app that provides user management, organizations, groups, authentication helpers, and multi-tenancy utilities.

Core code lives in `openwisp_users/`:

- `models.py` defines the swappable user, organization, group, and membership models.
- `api/` contains DRF views, serializers, authentication, permissions, filters, and throttling.
- `accounts/` customizes django-allauth account flows.
- `tests/` and `openwisp_users/tests/` provide the test project and app-level coverage.

The repository is a single Python package, not a monorepo.

## Tech Stack

- Python package built with `setuptools`
- Django app with django-allauth, DRF, Celery, Redis, and SQLite for local test/dev setup
- QA tooling driven by `openwisp-qa-check`
- Coverage via `coverage`
- GitHub Actions for CI and PyPI publishing

## Setup Commands

Use the same flow documented in `docs/developer/installation.rst` and mirrored in CI:

```sh
sudo apt-get install sqlite3 libsqlite3-dev openssl libssl-dev gettext
pip install -U pip wheel setuptools
pip install -r requirements-test.txt
pip install -e .[rest]
docker compose up -d
cd tests
./manage.py migrate
./manage.py createsuperuser
```

Notes:

- Redis is provided by `docker-compose.yml` on `localhost:6379`.
- The test project lives under `tests/` and uses `tests/openwisp2/settings.py`.
- Local DBs are SQLite files created in the repo root (`openwisp-users.db` and `openwisp-users-SAMPLE_APP.db`).

## Development Workflow

Run the local Django project from `tests/`:

```sh
cd tests
./manage.py runserver
```

Admin is available at `http://127.0.0.1:8000/admin/`.

If you need background workers for development features:

```sh
cd tests
celery -A openwisp2 worker -l info
celery -A openwisp2 beat -l info
```

Environment switches used by the project:

- `SAMPLE_APP=1` runs tests against the sample swapped app.
- `NO_SOCIAL_APP=1` disables `allauth.socialaccount` for targeted test coverage.
- `SELENIUM_HEADLESS=1` is used in CI for browser tests.

## Testing Instructions

Run the full repository test suite with:

```sh
./runtests
```

`./runtests` performs three passes:

1. Standard suite with coverage: `coverage run ./runtests.py --parallel`
2. Extensibility suite: `SAMPLE_APP=1 coverage run ./runtests.py --parallel`
3. Targeted admin test without socialaccount:
   `NO_SOCIAL_APP=1 coverage run ./tests/manage.py test testapp.tests.test_admin.TestUsersAdmin --parallel`

The script finishes with:

```sh
coverage combine
coverage xml
```

Useful focused commands:

```sh
./runtests.py --parallel
./runtests.py -k <test-name-or-pattern>
SAMPLE_APP=1 ./runtests.py --parallel
cd tests && ./manage.py test openwisp_users.tests.test_api.test_authentication --parallel
cd tests && ./manage.py test testapp.tests.test_views --parallel
```

Test layout:

- `openwisp_users/tests/` for package-level tests
- `openwisp_users/tests/test_api/` for API coverage
- `tests/testapp/tests/` for integration and multitenancy behavior
- `tests/openwisp2/sample_users/` for swapped-model/sample app coverage

Important runtime detail:

- Parallel tests use Django's local-memory cache.
- Non-parallel local runs use Redis-backed cache (`redis://localhost/0`).

## QA and Code Style

Run the repository QA checks with:

```sh
./run-qa-checks
```

This script:

- compiles translations with `django-admin compilemessages`
- runs `openwisp-qa-check` on the main app
- runs additional QA passes for `tests/testapp`
- runs a sample-app QA pass with `SAMPLE_APP=1`

Style conventions from repo config:

- Line length is 88 characters.
- Imports are sorted with `isort`.
- `flake8` ignores `W605`, `W503`, `W504`, and `E203`.
- Migrations and `setup.py`-style files are excluded from some lint rules.
- Follow existing Django/OpenWISP patterns instead of introducing new structure.

When editing code:

- Keep changes compatible with Django 4.2 through 5.2 and Python 3.10 through 3.13.
- Preserve swappable model support and multi-tenant permission behavior.
- Add or update tests for behavior changes.

## Build and Release

Build a distribution locally with:

```sh
python -m build
```

Legacy packaging also exists in `setup.py`:

```sh
python setup.py sdist bdist_wheel
```

GitHub Actions publishes to PyPI when a GitHub Release is published (`.github/workflows/pypi.yml`).

CI matrix (`.github/workflows/ci.yml`) runs:

- Python 3.10, 3.11, 3.12, 3.13
- Django 4.2, 5.0, 5.1, 5.2

Before opening or updating a PR, make sure both of these pass locally:

```sh
./run-qa-checks
./runtests
```

## Security and Auth Notes

- Authentication flows integrate with `django-allauth`.
- API auth includes token auth and request throttling in `openwisp_users/api/`.
- Do not hardcode secrets into committed settings files; use `tests/openwisp2/local_settings.py` only for local overrides.
- Be careful when changing cache invalidation, permissions, organization membership, and authentication backends; those areas affect tenant isolation.

## Pull Request Guidelines

Follow `.github/pull_request_template.md`:

- confirm you read the OpenWISP contributing guidelines
- manually test the change
- add or update tests
- update documentation when needed
- link the issue being closed

Keep PRs focused and avoid unrelated refactors.

## Troubleshooting

- If non-parallel tests fail unexpectedly, make sure Redis is running: `docker compose up -d`.
- If QA fails on translations, install `gettext`.
- If you change swapped-model behavior, run both the default suite and the `SAMPLE_APP=1` suite.
- For API/admin permission changes, check both `openwisp_users/tests/` and `tests/testapp/tests/` because coverage is split across package and integration tests.
