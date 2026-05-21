# AGENTS.md

## Project Overview

`openwisp-users` is the OpenWISP Django app that provides user management, organizations, groups, authentication helpers, and multi-tenancy utilities.

Core code lives in `openwisp_users/`:

- `models.py` defines the swappable user, organization, group, and membership models.
- `api/` contains DRF views, serializers, authentication, permissions, filters, and throttling.
- `accounts/` customizes django-allauth account flows.
- `tests/` and `openwisp_users/tests/` provide the test project and app-level coverage.

The repository is a single Python package, not a monorepo.

## Source of Truth

- For local development setup, database initialization, running the development server, background workers, and the baseline test command, use `docs/developer/installation.rst`.
- For developer-oriented package documentation, start from `docs/developer/index.rst`.
- For the CI-tested dependency installation, QA commands, test execution, environment variables, and Python/Django compatibility matrix, use `.github/workflows/ci.yml`.
- For release publishing details, use `.github/workflows/pypi.yml`.
- For contribution and PR expectations, use `.github/pull_request_template.md` and `CONTRIBUTING.rst`.

## Working Notes

- `openwisp_users/tests/` for package-level tests
- `openwisp_users/tests/test_api/` for API coverage
- `tests/testapp/tests/` for integration and multitenancy behavior
- `tests/openwisp2/sample_users/` for swapped-model/sample app coverage
- Use `.github/workflows/ci.yml` as the authoritative compatibility matrix for supported Python and Django versions.
- Preserve swappable model support and multi-tenant permission behavior.
- Add or update tests for behavior changes.
- For bug fixes, use TDD: add or update a regression test first, run it before the fix to confirm it fails for the expected reason, and make sure the failure message clearly describes the bug before implementing the fix.

## Instruction Priority

When instructions conflict:

1. CI workflows and repository configuration are authoritative.
2. Official documentation is authoritative for setup and workflows.
3. AGENTS.md provides supplemental repository-specific guidance.

## Security and Auth Notes

- Authentication flows integrate with `django-allauth`.
- API auth includes token auth and request throttling in `openwisp_users/api/`.
- Do not hardcode secrets into committed settings files; use `tests/openwisp2/local_settings.py` only for local overrides.
- Be careful when changing cache invalidation, permissions, organization membership, and authentication backends; those areas affect tenant isolation.

## Pull Request Guidelines

Keep PRs focused and avoid unrelated refactors. Follow the current checklist in `.github/pull_request_template.md`.

## Troubleshooting

- If setup, QA, or test commands need adjustment, check the relevant docs page first and then verify the current CI workflow.
- If you change swapped-model behavior, tenant isolation, auth flows, or admin/API permissions, ensure coverage includes both package-level tests and integration tests.
