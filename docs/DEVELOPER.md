# Developer guide

Everything needed to run, debug and deploy the platform. Keep it current: any change to
setup, services, environment variables or debugging steps updates this file in the same
commit.

Stack: Python 3.14, Django 6, PostgreSQL, Redis, Celery, Tailwind (django-tailwind-cli),
HTMX + Alpine (CSP build). Everything runs in Docker; `uv` runs host-side tools.

## 1. Run it locally

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), make, git.

```bash
git clone <repo> && cd modular-saas
uv sync                       # host tools: black, isort, flake8, mypy, import-linter
# .envs/.local/.django and .envs/.local/.postgres: copy from a teammate (git-ignored)
make build                    # Docker images
make up                       # Postgres, Redis, Mailpit, Django, Celery, Tailwind watcher
make migrate                  # migrate_schemas: public schema, then every workspace
docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser
```

Multi-tenancy (django-tenants): the root domain (`localhost:8000`) serves the marketing
site, signup and admin; each workspace has its own subdomain and Postgres schema
(`acme.localhost:8000` → schema `ws_acme`). Users and memberships are shared; business
data lives only in workspace schemas.

| URL | What |
|---|---|
| http://localhost:8000 | Root domain: marketing site, signup (open locally, closed by default elsewhere), login |
| http://localhost:8000/signup/ | Create a workspace: SIRET, then account, then email code (Mailpit), then you land in `<name>.localhost:8000` |
| `http://<slug>.localhost:8000` | A workspace. Chrome and Firefox resolve `*.localhost`; for Safari add the host to `/etc/hosts` |
| http://localhost:8000/admin/ | Django admin (local URL; production uses `DJANGO_ADMIN_URL`) |
| http://localhost:8025 | Mailpit: every email the app sends (verification codes, resets) |
| http://localhost:5555 | Flower: Celery tasks (`CELERY_FLOWER_USER` / `_PASSWORD` from `.envs/.local/.django`) |

Stop with `make down`.

## 2. Daily commands

| Command | Does |
|---|---|
| `make check` | The gate: lint, types, Django check, migration check, tests + coverage. Must pass before a commit |
| `make migrate` | `migrate_schemas` (never plain `migrate`): public schema, then every workspace |
| `make test-one T=path::test_name` | One test, no coverage |
| `make fmt` | black + isort |
| `make messages` | Extract and compile translations (fr, en). Then fill `locale/fr_FR/LC_MESSAGES/django.po` |
| `make security` | bandit + pip-audit |
| `make css` | Build Tailwind once (the `tailwind` container watches in dev) |

Tests, Django checks and migrations run inside the `django` container; lint and mypy run
on the host through `uv`.

## 3. Debugging in dev

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError` for a package that is in `pyproject.toml` | Containers still run the old image. `make build && make up` (`docker compose restart` reuses the old container) |
| Mailpit at :8025 is empty although emails were "sent" | Another Mailpit (Homebrew) holds port 8025. `brew services stop mailpit`, then `docker compose -f docker-compose.local.yml restart mailpit` |
| `NoReverseMatch` right after pulling or adding a URL | The dev server did not reload `urls.py`: `docker compose -f docker-compose.local.yml restart django` |
| New Tailwind classes have no effect | Check `docker compose ... logs tailwind`; templates must sit under `apps/**/templates` |
| A test passes alone but fails in the full run | Leaked state between tests. The root `conftest.py` resets the active language; add similar resets there |
| Tests fail with "A schema named 'ws_…' already exists" | An aborted run left a workspace schema in the reused test DB. Rebuild it once: `docker compose -f docker-compose.local.yml run --rm django pytest --create-db` |
| "No access to this workspace" (403) | Signed in as a user who is not a member. Sign out, or add a `Membership` in the admin |
| "This sign-in link has expired" | Handoff links into a workspace work once, for 60 s. Sign in again on the root domain |
| A workspace subdomain shows the marketing site | No `Domain` row for that host (the root domain is the fallback). Check the admin's Domains |
| `NoReverseMatch` for `admin:` (or another root-only page) in a test | Outside a request, `reverse()` uses the workspace URLconf. Add `pytestmark = pytest.mark.usefixtures("public_urls")` |
| "Un instant, s'il vous plaît" (429) while testing | Rate limits (waitlist 5/h per IP, allauth code resends). Restart Django or clear the cache: `... run --rm django python manage.py shell -c "from django.core.cache import cache; cache.clear()"` |
| Need a verification or sign-in code | Mailpit, or `curl -s localhost:8025/api/v1/messages` |
| SIRET lookup never shows | Expected without `SIRENE_API_KEY`: lookup is off and signup uses manual entry |
| Slow page / N+1 queries | Django Debug Toolbar is on in local settings (right edge of the page) |
| Translation shows in English | `make messages`, fill the empty or fuzzy `msgstr`, run again. `tests/test_translations.py` fails on missing ones |

Run a shell: `docker compose -f docker-compose.local.yml run --rm django python manage.py shell`.
Database: `docker compose -f docker-compose.local.yml exec postgres psql -U <POSTGRES_USER> <POSTGRES_DB>`.

## 4. Project rules in one minute

- Read `CLAUDE.md` (working rules) and `docs/ARCHITECTURE.md` sections 4, 5, 8 before adding an app.
- Layers: view → form → service → repository → model. Feature apps never import each other;
  they talk through `apps.core.events`. `make lint` enforces this (import-linter).
- Country-specific logic lives in `apps/countrypacks/<code>/`. Money is `apps.core.money.Money`.
- User-facing text: English source, `gettext`, French translation required.
- Progress and decisions: `docs/PROGRESS.md`.

## 5. Production

### Environment variables

Required (no default, the app will not start without them):

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Long random string |
| `DJANGO_ADMIN_URL` | Secret admin path, e.g. `x8f2k/` (trailing slash) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Or one `DATABASE_URL` |
| `BREVO_API_KEY` | Transactional email (anymail) |
| `DJANGO_AWS_ACCESS_KEY_ID`, `DJANGO_AWS_SECRET_ACCESS_KEY`, `DJANGO_AWS_STORAGE_BUCKET_NAME` | S3-compatible storage (Scaleway, EU) |
| `SENTRY_DSN` | Error reporting |
| `CELERY_FLOWER_USER`, `CELERY_FLOWER_PASSWORD` | Flower basic auth (read by its start script) |

Set these too (defaults are wrong for production):

| Variable | Default | Set to |
|---|---|---|
| `DJANGO_ALLOWED_HOSTS` | `example.com` | Root domain and all workspaces, e.g. `app.example.fr,.app.example.fr` |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `postgres`, `5432` | Managed database host |
| `REDIS_URL` | `redis://redis:6379/0` | Cache, Celery broker, rate limits |
| `SITE_DOMAIN` | `localhost:8000` | Root domain, e.g. `app.example.fr`. **Set before the first `migrate_schemas`**: it seeds the public tenant's domain. Workspaces get `<slug>.<SITE_DOMAIN>`. Also shown in emails |
| `DJANGO_DEFAULT_FROM_EMAIL`, `DJANGO_EMAIL_SUBJECT_PREFIX` | cookiecutter values | Real sender and prefix |
| `DJANGO_AWS_S3_REGION_NAME`, `DJANGO_AWS_S3_CUSTOM_DOMAIN` | none | Bucket region / CDN domain |
| `SIRENE_API_KEY` | empty (lookup off) | INSEE key: portail-api.insee.fr → application with "Simple" security → subscribe to API Sirene. Confirm the header name in the portal docs matches `SireneRegistry.KEY_HEADER` |

Feature switches:

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_ACCOUNT_ALLOW_REGISTRATION` | `False` | Open sign-up (beta launch) |
| `WAITLIST_ENABLED` | `False` | Waitlist form. Only after the legal notice and privacy pages are filled in |
| `BREVO_WAITLIST_LIST_SAAS`, `BREVO_WAITLIST_LIST_BOILERPLATE`, `BREVO_DOI_TEMPLATE_ID`, `WAITLIST_CONFIRMED_URL` | 0 / empty | Brevo lists, double opt-in template, post-confirmation URL |
| `WAITLIST_RATE_LIMIT` | `5/h` | Per IP |
| `TENANT_UNIQUE_TAX_ID` | `True` | One workspace per SIRET (others are told to ask for an invitation) |
| `SIGNUP_LOOKUP_RATE_LIMIT` | `10/m` | Signup company step, per IP (protects the shared Sirene quota) |

Optional: `SENTRY_ENVIRONMENT`, `DJANGO_SENTRY_LOG_LEVEL`, `CONN_MAX_AGE`,
`DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_PRELOAD`, `DJANGO_ADMIN_FORCE_ALLAUTH`.

### Deploy steps

The image compiles translations and builds Tailwind; the container runs `collectstatic` at
start. **Migrations are not automatic**:

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml run --rm django python manage.py migrate_schemas
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml run --rm django python manage.py check --deploy
```

Workspaces live on subdomains: point a **wildcard DNS record** (`*.app.example.fr`) and
the root (`app.example.fr`) at the server, and use a **wildcard TLS certificate**
(Let's Encrypt DNS-01 challenge; Traefik supports it).

### Before going live

- [ ] `check --deploy` is clean
- [ ] Wildcard DNS and wildcard certificate in place; `DJANGO_ALLOWED_HOSTS` includes `.app.example.fr`
- [ ] Legal notice and privacy pages filled in (`apps/marketing/templates/marketing/`)
- [ ] RGPD register lists sub-processors and recipients: Scaleway, Brevo, Sentry, INSEE (SIRET lookups)
- [ ] Production deployment target is not decided yet (Scaleway, EU). `docker-compose.production.yml` is the cookiecutter Traefik setup until then
