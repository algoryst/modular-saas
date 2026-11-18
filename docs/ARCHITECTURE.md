# ARCHITECTURE.md
# Modular Multi-Tenant Django Platform: Technical Reference
# Version 3 (legal-minimum plan), 18 November 2026

Companion files: PRODUCTS.md (what we sell), PROGRESS.md (checklist), LEGAL.md (founder legal path).

---

## 1. Principles (non-negotiable)

1. One codebase, many products. Every product is a composition of apps.
2. SOLID and DRY. No logic duplicated; no class with two reasons to change.
3. Strict layers. Views → Forms → Services → Repositories → Models.
4. Cross-module communication by **events**, never direct imports between feature apps.
5. Every line is tested. No merge with failing CI.
6. Compliance is a feature, not an afterthought, but we claim only what we deliver ("aide à la conformité", "connecté à une plateforme agréée").

## 2. Stack (locked)

| Concern | Choice |
|---|---|
| Language / framework | Python, Django, DRF |
| Project template | django-cookiecutter |
| DB | PostgreSQL |
| Multi-tenancy | django-tenants (schema per tenant; public schema holds only Tenant and Domain) |
| Auth | django-allauth, django-two-factor-auth, django-axes, django-guardian |
| Payments | dj-stripe; Stripe Checkout / Payment Links, Stripe Connect Standard for tenant collection (we never hold funds) |
| Async | Celery + Redis |
| Files | MinIO / django-storages (S3-compatible, EU region) |
| Email | Brevo via django-anymail |
| PDF | WeasyPrint |
| Search | django-watson |
| Audit / history | django-auditlog, simple-history, activity-stream |
| State machines | django-fsm |
| Misc | django-taggit, django-import-export, drf-spectacular, simplejwt |
| Admin | django-unfold |
| Frontend | Django templates + Tailwind + HTMX + Alpine.js + django-template-partials. **No React/SPA.** |
| JS widgets | FullCalendar, SortableJS, Chart.js, Trix, Tom Select, Flatpickr, Lucide icons |
| Design | Inter font, Zinc + Blue semantic tokens, light mode only in v1 |
| Mobile | Responsive web only in v1; no native app |
| Hosting | Scaleway (EU) |
| Analytics (own site) | Cookieless, CNIL-exempt configuration (Matomo verified; verify any alternative before use). No cookie banner |
| Billing for the boilerplate | Merchant of record (Paddle, or Lemon Squeezy / Stripe Managed Payments), see LEGAL.md |

## 2b. Global-Ready Design (France first, UK second)

Market order: **France (launch) → United Kingdom (second) → others only on pull.** The architecture is global from Phase 1; the marketing is not.

| Concern | Rule |
|---|---|
| Language | English source strings, gettext; French first translation (launch), `en-GB` is the base for UK. Native review before marketing in any language |
| Money | `Decimal` + ISO 4217 currency on every amount; per-tenant default currency, per-document currency; EUR and GBP at launch |
| Locale | Per-tenant country, timezone, date/number/address formats; timezone-aware datetimes everywhere |
| Tax | Tax rates, rules and mandatory invoice mentions are **data** loaded from the tenant's country pack, never hard-coded |
| Numbering | Per-tenant, per-series, gap-free; series configurable per country |
| Company IDs | `TaxIdentity` model: country + type (SIRET/SIREN/TVA FR, Companies House number, UK VAT number) + value + validator per country |
| Payments | Stripe Connect Standard; verify coverage per country before promising |
| Legal docs | Terms/DPA templates versioned per jurisdiction (FR, UK) |
| Data residency | EU hosting (Scaleway) at launch; UK customers: UK GDPR transfer position to confirm (see LEGAL.md) |

### Country Packs (open/closed principle)

```
countrypacks/
  base.py        # CountryPack protocol
  fr/            # France: rates, mentions (293 B), FEC export, PA adapter, SIRET validator, FR legal templates
  gb/            # UK: rates, VAT-number/Companies-House validators, UK invoice mentions, UK legal templates, (later) Peppol adapter
  generic/       # fallback: manual tax lines, no e-invoicing
```

`CountryPack` interface: `tax_rates()`, `invoice_mentions(tenant)`, `validate_tax_identity()`, `numbering_rules()`, `einvoicing_adapter()` (optional), `accounting_export()` (optional), `legal_templates()`, `locale_defaults()`.
Services depend on the interface; adding a country never edits existing code. Every pack passes the same contract test suite. Invoicing (Phase 3b) is the only module that consults packs deeply; CRM, quotes, e-signature, projects, portal are country-neutral.

UK specifics to implement in the `gb` pack (confirm each with a UK accountant before launch unless marked ✅): VAT-registered vs not invoice variants, GBP, UK VAT number validation, mandatory B2B e-invoicing planned from April 2029 via Peppol ✅ (design the adapter interface now; build later).

## 3. Apps by Phase

| Phase | Apps |
|---|---|
| 1 Foundation | core, tenants, accounts, billing, notifications, audit, dashboard, settings_app |
| 2 Boilerplate | packaging, docs, demo data |
| 3a CRM and Sales | contacts, companies, deals, pipelines, activities, quotes, esignature, catalogue (basic) |
| 1 (add) | countrypacks (base + fr + generic), i18n setup, currency/locale settings |
| 3b Invoicing | invoicing (immutable invoices, credit notes), pa_connector (France partner PA adapter), vat_summary (récapitulatif TVA, FEC export, via the fr pack) |
| 6b UK launch | countrypacks/gb, UK legal templates, UK invoicing mentions, GBP pricing, en-GB copy |
| 4 Operations | projects, tasks, timetracking, calendar, files |
| 5 Commerce | catalogue (full), orders, inventory, subscriptions, payments (Stripe Connect) |
| 5b RGPD | rgpd (registers, DPA templates, data-subject-request tracker, retention rules) |
| 6 Products | customerportal, linkinbio, rgpdtool (standalone shells), api_auth, api_audit, api_notify |

## 4. Layers and Rules

| Layer | Allowed | Forbidden |
|---|---|---|
| View | Parse request, call form and service, render | Business logic, ORM queries |
| Form | Validation, field cleaning | DB writes beyond `save()` delegating to service |
| Service | Business rules, transactions, emit events | HTTP objects, templates |
| Repository | All ORM queries, tenant-scoped | Business decisions |
| Model | Fields, constraints, tiny derived properties | Cross-app calls |
| Event handler | React to events from other apps | Synchronous blocking work (use Celery) |

Standard per-app layout:

```
app/
  models.py  repositories.py  services.py  forms.py  views.py  urls.py
  events.py  handlers.py  admin.py  api/(serializers.py, views.py)
  templates/app/  tests/(test_models, test_repositories, test_services,
                         test_forms, test_views, test_events, test_api)
```

## 5. Core Abstractions

Abstract models: TimeStamped, UUID, TenantScoped, SoftDelete, CreatedBy, Ordered.
Mixins: Audit, Search, Notification, Export.

Key models: Tenant, Domain, User, Membership, Contact, Company, Deal, Pipeline, Stage, Activity, Quote, QuoteLine, SignatureRequest, SignatureAuditLog, Invoice, InvoiceLine, CreditNote, Project, Task, TimeEntry, Product, Order, Subscription, ProcessingRecord, DataSubjectRequest.

### E-signature (simple electronic signature only)

- SignatureRequest: quote FK, signer name/email, single-use expiring token, status (FSM: sent → viewed → signed / declined / expired), SHA-256 hash of the PDF at send time.
- SignatureAuditLog: append-only; events (sent, viewed, signed, declined), timestamp, IP, user agent, document hash.
- Signed PDF stored with a certificate page.
- Product copy says "signature électronique simple". Never "qualifiée" or "avancée". If higher assurance is ever demanded, integrate a qualified provider (for example Yousign) rather than build.

### Invoicing (Phase 3b)

- Invoices are **immutable once issued**. Corrections go through CreditNote. Gap-free numbering per tenant per year (DB sequence + unique constraint).
- Mandatory mentions live in tenant settings, including the VAT-franchise mention, **configurable** (default « TVA non applicable, art. 293 B du CGI »; re-check wording for 2027).
- Formats: Factur-X (PDF/A-3 + CII XML); UBL/CII through the PA connector.
- `pa_connector`: interface `PlatformAdapter` (send_invoice, fetch_status, receive_invoice, report_payment). One adapter per partner PA. We do **not** become a PA. Claim "connecté à une plateforme agréée" only when a live adapter exists.
- Retention: documents kept for the legal period; personal fields anonymisable without deleting the document.
- "Mark as paid" is a status change (method, date, reference). No till/POS features. NF525 applicability is an open question (LEGAL.md).
- `vat_summary`: récapitulatif TVA and FEC export only. No filing, no tax advice.

### Tenant signup

B2B only. SIRET required. Email verification mandatory. Terms (CGV/CGU + DPA annex) acceptance stored with timestamp and version.

### RGPD module

ProcessingRecord (Art. 30 register for the tenant's use), DataSubjectRequest tracker, retention-rule helper, DPA template generator. Always labelled "aide à la conformité" with a disclaimer. Platform-level: our own Art. 30(2) processor register and public sub-processor list (Scaleway, Brevo, Stripe, Sentry) kept in `docs/compliance/`.

### Link in Bio (Phase 6)

Public pages are user-generated. Required: terms of use, abuse-report endpoint, admin takedown action, verified email. Paid-first with trial; free tier only after moderation tooling exists.

## 6. SOLID / DRY in Practice

- Single responsibility: one service class per use case (`CreateQuote`, `SendQuoteForSignature`).
- Open/closed: PlatformAdapter, PaymentProvider, StorageBackend, Notifier are interfaces; add implementations, never edit callers.
- Liskov: adapters pass the same contract tests.
- Interface segregation: small protocols over fat base classes.
- Dependency inversion: services receive repositories and adapters through constructors.
- DRY: shared UI partials, shared base models, one place for money/VAT arithmetic (`core/money.py`, Decimal only).

## 7. Code Quality

black, isort, flake8, mypy (strict on services and repositories), bandit, pip-audit, pre-commit hooks. Type hints everywhere. Money is always `Decimal`, never float.

## 8. Testing Strategy

| Layer | Tool | Coverage target |
|---|---|---|
| Services, repositories | pytest | 90% |
| Models, forms | pytest | 80% |
| Views, API | pytest + DRF client | 80% |
| Templates / E2E | Playwright | 70% of critical flows |

Mandatory tests: tenant isolation, permissions, invoice immutability and numbering, signature token expiry and hash integrity, event handlers, migrations forward and backward. factory_boy for data, freezegun for time.

## 9. CI/CD

lint (black, isort, flake8) → mypy → bandit + pip-audit → pytest + coverage gate → `makemigrations --check` → docker build → staging → Playwright smoke → manual promote. Dependabot weekly.

## 10. UI Design System

- Tokens: Zinc neutrals, Blue 600 primary, semantic success / warning / danger. 4 px grid, 8 px radius, one shadow level.
- Components (template partials): button, input, select, table, card, modal, toast, empty state, kanban column, badge, tabs.
- Rules: one primary action per screen; empty states explain the next step; single-column forms; plain French labels; keyboard accessible; WCAG AA.
- HTMX for partial updates, Alpine.js for local state only.

## 11. French Compliance Requirements (as built)

| Topic | Requirement in code |
|---|---|
| E-invoicing | PA-connected, not a PA. Reception from 1 Sept 2026; issuance and e-reporting for small businesses from 1 Sept 2027 |
| Invoice mentions | Configurable; immutable; credit notes |
| RGPD | Art. 28 DPA, Art. 30(2) register, sub-processor list, export/delete endpoints, breach log |
| Cookies | Strictly necessary only; exempt analytics |
| Hosting | EU region only |
| Security | 2FA, axes, audit log, encrypted backups, secrets in env |
| LCEN | Mentions légales page with host details |
| E-signature | Simple only; audit trail |

## 12. Claude Code Setup and Session Prompt

Repo layout: `CLAUDE.md` at the root (auto-loaded, under 200 lines, guidance only); `.claude/settings.json` and `.claude/hooks/` (enforced rules); `Makefile` (`make check` is the single gate); `.importlinter` (architecture contracts); the five plan documents in `docs/`. Everything that must never be violated is a hook, deny rule or CI check, not a CLAUDE.md sentence. Details and ready-to-copy files: ENFORCEMENT.md. Rules text: CLAUDE.md.

Short session prompt (CLAUDE.md already carries the rules):

```
Read ARCHITECTURE.md, PRODUCTS.md, PROGRESS.md and LEGAL.md.
Work on the first unchecked item in PROGRESS.md.
Follow the layers and file structure strictly. Write tests first for services.
Run the full CI locally before declaring done. Update PROGRESS.md and the
session log. Never import across feature apps; use events.
```
