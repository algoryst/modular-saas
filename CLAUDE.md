# CLAUDE.md

Place this file at the repository root. Claude Code loads it every session. Keep it under 200 lines.
Rules that can never bend are enforced by hooks and deny rules (see docs/ENFORCEMENT.md), not by this file.

## Project

Modular multi-tenant Django platform that yields several products from one codebase.
Markets: France first, UK second, global-ready (country packs, gettext, multi-currency). B2B only.
Plan documents: docs/ARCHITECTURE.md, docs/PRODUCTS.md, docs/PROGRESS.md, docs/LEGAL.md.
Read docs/ARCHITECTURE.md sections 4, 5 and 8 before creating or restructuring an app.
The plan documents are locked decisions. If one looks wrong, say so and wait. Do not edit them except to tick PROGRESS.md boxes and add session-log rows.

## Commands

Run these through make. All of them must pass before you say a task is done.

- `make check` runs the whole gate: lint, types, django check, migration check, tests
- `make fmt` black + isort
- `make lint` black --check, isort --check, flake8, import-linter
- `make types` mypy
- `make security` bandit + pip-audit
- `make migrations-check` `python manage.py makemigrations --check --dry-run`
- `make test` pytest with coverage gates
- `make test-one T=path::name` one test, no coverage
- `make up` / `make down` docker compose (Postgres, Redis, MinIO)
- `make messages` makemessages + compilemessages for fr and en

## Workflow

- Plan first when a change touches 3 or more files, adds a model, an app, a dependency or an endpoint. Show the plan, wait for approval.
- Write the failing test first for services, repositories and bug fixes.
- Touch only files the task needs. No opportunistic refactors. Log unrelated problems at the end of your reply under "Not now".
- State assumptions explicitly. If a requirement is ambiguous, ask one concise question.
- Find root causes. No temporary patches, no `# noqa` or `# type: ignore` without a one-line reason.
- Commit after each completed item with a conventional message (feat, fix, test, chore, docs). Never push.

## Approval required before you do any of these

- Add or upgrade a dependency
- Create or change a model, or create a migration
- Change settings: INSTALLED_APPS, MIDDLEWARE, DATABASES, AUTH_*, SHARED_APPS, TENANT_APPS, CELERY_*, security settings
- Change auth, permissions, URL names or the public API contract
- Change CI, Docker or deployment config
- Delete a test or lower a coverage threshold (never do this; ask instead)

## Architecture rules

- Layers: view -> form -> service -> repository -> model. Views parse and render only. ORM queries live only in repositories. Business rules live only in services.
- Feature apps never import each other. Cross-app effects go through events in `core.events`. Import-linter enforces this.
- Services take dependencies (repositories, adapters, clock) through the constructor. One service class per use case.
- External systems sit behind interfaces: `PlatformAdapter`, `PaymentProvider`, `StorageBackend`, `Notifier`. Add implementations, never edit callers.
- Country-specific tax, invoice mentions, ID validation and legal templates live in `countrypacks/<code>/`. Never hard-code France or UK logic elsewhere.
- Money is `Decimal` plus a currency code through `core.money`. Never float. Never round outside `core.money`.
- Every app follows the standard file layout in docs/ARCHITECTURE.md section 4.
- Shared UI is a template partial. Do not copy-paste markup.

## Django rules

- Prefer class-based views and DRF viewsets that match the existing app. Keep views under about 30 lines.
- Every query that spans relations uses `select_related` or `prefetch_related`. Filter in the database, never in Python. Add a `django_assert_num_queries` test for list views.
- No raw SQL unless a repository needs it; then parameterize. Never build SQL with f-strings.
- Validate input with forms or serializers, never from `request.POST` or `request.data` directly.
- Use Django's auth and password hashing. No custom password handling.
- Atomic transactions in services (`transaction.atomic`). Send emails, call Stripe and enqueue Celery tasks with `transaction.on_commit`.
- Never edit a migration that is already committed. Fix forward with a new migration. Give data migrations a reverse function.
- Use `gettext` / `gettext_lazy` for every user-facing string. No literal French or English in Python or templates outside translation files.
- Datetimes are timezone-aware. Use an injected clock, never `datetime.now()` in services.
- Settings come from environment variables. No secrets in the repo. `DEBUG` is false by default.

## User experience (priority)

- Making the user's life simpler is a priority: fewer steps, fields and decisions, plain words, no dead ends.
- When you see a change that would do that, even outside the current task, propose it with its trade-off. Implement it only after the user confirms.

## Multi-tenancy (django-tenants)

- Public schema holds Tenant, Domain, User, Membership and the auth, session and allauth tables. Business data lives only in tenant schemas (feature apps go in TENANT_APPS). An app listed in neither SHARED_APPS nor TENANT_APPS gets no tables.
- Run `migrate_schemas`, never plain `migrate`, in docs, scripts and CI.
- Outside a request, wrap tenant work in `tenant_context` or `schema_context`. Code after the block runs in whatever schema was active before it.
- Every Celery task receives a tenant identifier and sets the tenant context itself. Test this.
- Tests that touch tenant data use django-tenants test cases. Write a tenant-isolation test for every new tenant model and view: tenant A can never read or write tenant B.
- Creating a tenant creates its schema and runs migrations. Keep tenant creation in one service.
- `delete_tenant` drops the schema even when `auto_drop_schema` is False. Never call it outside an explicit, tested service.
- Locally use `*.localhost` domains.

## Frontend (Django templates, Tailwind, HTMX, Alpine)

- No React, no SPA, no build-time framework. Tailwind classes only; no custom CSS unless a token is missing.
- HTMX returns partials. Use django-template-partials; in the view, render the partial when `request.htmx`, the full page otherwise.
- Send the CSRF token with `hx-headers` on `<body>` using `{{ csrf_token }}`.
- Self-host htmx, Alpine and every extension in static files. No CDN scripts, no extensions from CDNs.
- Alpine holds local UI state only. No business logic and no fetch calls in Alpine; use HTMX.
- Escape user content. No `|safe` or `mark_safe` on user-controlled data. Wrap untrusted injected HTML in `hx-ignore`. Pass data to JS with `json_script`.
- Avoid inline scripts and `eval`-style attributes (`hx-on`, `js:` values) so a strict CSP works.
- Follow the design tokens in docs/ARCHITECTURE.md section 10. One primary action per screen. Every empty state explains the next step. Forms are single column.

## Security

- Enable and keep `python manage.py check --deploy` clean for production settings.
- Secure cookies, HSTS, SSL redirect, X-Frame-Options DENY or SAMEORIGIN, nosniff, strong password validators, django-axes, 2FA for staff.
- Content Security Policy: Django built-in middleware on version 6 or later, otherwise django-csp. Start in report-only, then enforce.
- Custom admin URL. Staff accounts require 2FA.
- Uploads: validate size, extension and content type, store in S3-compatible storage, never serve from the app domain.
- Rate-limit login, signup, password reset and signature-token endpoints.
- Signature tokens are single-use, expiring and stored hashed.
- Never log secrets, tokens, full request bodies or personal data.

## Compliance rules (claims in code, copy and tests)

- Say "signature électronique simple". Never "qualified" or "advanced".
- Say "connecté à une plateforme agréée" only when a live adapter exists. We are not a PA.
- Say "aide à la conformité" for RGPD features. Never "garantit".
- Issued invoices are immutable. Corrections are credit notes. Numbering is gap-free per tenant and series.
- The VAT-franchise mention is a configurable string, not a literal.
- No point-of-sale or cash-register features. "Mark as paid" is a status change only.
- B2B only. SIRET (or the country's equivalent tax identity) is required at signup.
- No analytics scripts, trackers or cookies beyond strictly necessary on our own site, except the configured CNIL-exempt analytics tool.

## Testing

- pytest, pytest-django, factory_boy, freezegun. No fixtures files for domain data; use factories.
- Coverage gates: services and repositories 90%, models and forms 80%, views and API 80%.
- Test names describe behaviour: `test_<unit>_<condition>_<result>`.
- Mock only at boundaries (Stripe, Brevo, PA adapter, storage). Never mock the ORM. Adapters pass the shared contract test suite.
- Required tests: tenant isolation, permissions per role, immutability of issued invoices, numbering without gaps, signature token expiry and hash integrity, event handlers, migrations forward and backward.
- A bug fix starts with a failing regression test.
- Playwright covers critical flows only: signup, quote to signature, invoice issue.
- Tests must be deterministic: no sleeps, no network, no dependence on order or wall-clock time.

## Code style

- black, isort, flake8, mypy. Type hints on every function. mypy strict for services and repositories.
- Functions stay short and do one thing. Prefer composition over inheritance. No god classes.
- Comments explain why, not what. No commented-out code. No TODO without an issue reference or a PROGRESS.md item.
- No new abstraction until a second use exists, except the interfaces listed above.

## Definition of done

1. `make check` passes with no new warnings.
2. New code has tests and the coverage gates hold.
3. Migrations exist for every model change and `make migrations-check` is clean.
4. User-facing strings are translated (fr) and `make messages` is clean.
5. docs/PROGRESS.md box ticked and a session-log row added.
6. docs/DEVELOPER.md updated when setup, services, environment variables or debugging steps change.
7. For UI changes: run the app and exercise the page in a browser before saying it works.
8. Reply with what changed, what is next, and any "Not now" items. No recap of steps.

## Session start

Read docs/PROGRESS.md and take the first unchecked item. Restate the task in one or two sentences. After a context compaction, re-read docs/PROGRESS.md and the files you were editing before resuming.
