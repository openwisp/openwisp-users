# AGENTS.md

## Project Overview

`openwisp-users` is the OpenWISP Django app that provides user management, organizations, groups, authentication helpers, and multi-tenancy utilities.

Core code lives in `openwisp_users/`:

- `models.py` defines the swappable user, organization, group, and membership models.
- `api/` contains DRF views, serializers, authentication, permissions, filters, and throttling.
- `accounts/` customizes django-allauth account flows.
- Tests live in `openwisp_users/tests/`, `openwisp_users/tests/test_api/`, `tests/testapp/tests/`, and `tests/openwisp2/sample_users/`.

## Source of Truth

- Use `docs/developer/installation.rst` and `docs/developer/index.rst` for local setup, services, and baseline test commands.
- Use `.github/workflows/ci.yml` for CI-tested dependencies, QA/test commands, env vars, and supported Python/Django versions.
- Use GitHub issue/PR templates when asked to open issues or PRs.

Follow the DRY principle: do not duplicate information or code across files.

If instructions conflict, repository config and CI workflows win first, official docs next, and this file is supplemental.

## Development Notes

- Keep changes focused. Avoid unrelated refactors and formatting churn.
- Preserve swappable model support, public APIs, migrations, and multi-tenant permission behavior unless explicitly required.
- Mark user-facing strings for translation with Django i18n helpers in Django code.
- Place imports at the top of the file. Only defer imports when necessary (e.g., Django model imports inside functions or methods where the app registry is not yet ready).
- Avoid unnecessary blank lines inside function and method bodies.
- Update docs when behavior, settings, public APIs, setup steps, or supported versions change.

## Testing and QA

- Add or update tests for every behavior change.
- For bug fixes, write the regression test first, run it against the unfixed code, confirm it fails for the expected reason, then implement the fix.
- Use targeted tests while iterating, then run the documented full test command before considering the change complete.
- Run `openwisp-qa-format` after editing when available.
- Run `./run-qa-checks` when present. Treat failures as blocking unless confirmed unrelated and reported.
- Prefer in-process tests so coverage tools can measure changed code.

## Security and Auth Notes

- Authentication flows integrate with `django-allauth`; API auth includes token auth and request throttling in `openwisp_users/api/`.
- Be careful with cache invalidation, permissions, organization membership, authentication backends, and tenant isolation.
- If you change swapped-model behavior, tenant isolation, auth flows, or admin/API permissions, cover both package-level and integration tests.
- Write comments and docstrings only when they explain why code is shaped a certain way. Put comments before the relevant code block instead of scattering them inside it.

## Troubleshooting

- If setup, QA, or tests fail, check docs first, then compare with CI. If commands diverge, follow CI.
