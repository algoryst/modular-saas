# PROGRESS.md
# Master Checklist
# Version 3 (legal-minimum plan), 18 November 2026

Rule: work the first unchecked item. Tests with every item. Update the session log.

---

## Locked Decisions

- **Markets: France first, UK second, others on pull. Architecture global-ready from Phase 1 (country packs, i18n, multi-currency).**
- Django + DRF, django-tenants, PostgreSQL, HTMX + Alpine + Tailwind, no React, light mode only, responsive web only
- Horizontal French SME platform; no verticals
- B2B only, SIRET at signup
- E-invoicing via partner PA; we are not a PA
- Simple e-signature only
- Stripe Checkout/Payment Links + Connect Standard; never hold funds
- Merchant of record for the boilerplate
- Cookieless, CNIL-exempt analytics; no banner
- Micro-entreprise first; EURL/SASU decision by Month 6

## Phase 0: Legal Minimum + Setup (Week 0–1)

- [ ] Register micro-entreprise (Guichet unique, free)
- [ ] Ask accountant: BIC/BNC (30 min)
- [ ] Business bank account
- [ ] INPI name search, buy domain
- [ ] Mentions légales page (LCEN) with host details
- [ ] Privacy policy
- [ ] Boilerplate licence terms / CGV
- [ ] Analytics: CNIL-exempt tool (Matomo CNIL config verified; verify alternatives)
- [ ] Merchant of record account (compare Paddle vs Lemon Squeezy / Stripe Managed Payments)
- [ ] One-page RGPD register spreadsheet (controller tab + sub-processor tab)
- [x] Repo, cookiecutter, CI pipeline, pre-commit, coverage gates
- [x] Claude Code guardrails: CLAUDE.md at root, `.claude/settings.json` + hooks (ENFORCEMENT.md), Makefile `make check`, `.importlinter`; run the day-one verification list (ENFORCEMENT.md §9)
- [x] Waitlist landing page

## Phase 1: Foundation (Weeks 1–8)

- [x] W1 core: base models, mixins, money.py (Decimal + currency), event bus
- [ ] W1 i18n: gettext setup, English source strings, French translation, locale/timezone settings
- [ ] W1 countrypacks: `CountryPack` protocol, contract test suite, `generic` and `fr` packs (skeleton)
- [ ] W2 TaxIdentity model with per-country validators (SIRET first)
- [ ] W2 tenants: django-tenants, signup with SIRET, isolation tests
- [ ] W3 accounts: allauth, 2FA, axes, guardian, memberships and roles
- [ ] W4 billing: dj-stripe, plans, Checkout, webhooks
- [ ] W5 notifications: Brevo, templates, Celery
- [ ] W6 audit + settings_app
- [ ] W7 dashboard shell + UI design-system partials
- [ ] W8 demo data, docs, E2E smoke

## Phase 2: Boilerplate (Weeks 7–9)

- [ ] Package and document the boilerplate
- [ ] Installation guide, example app
- [ ] Sell via MoR; first-sale target Week 8–9

## Phase 3a: CRM and Sales (Months 3–5)

- [ ] Contacts, companies, tags, import/export
- [ ] Pipelines, deals (kanban with SortableJS)
- [ ] Activities, notes, search
- [ ] Product catalogue (basic)
- [ ] Quotes with PDF (WeasyPrint)
- [ ] E-signature: SignatureRequest, token flow, audit log, signed PDF
- [ ] Gate 2 legal: DPA annex, Art. 30(2) register, sub-processor list, B2B CGV, breach procedure
- [ ] Beta with 3–5 users, then launch (Month 5)

## Phase 3b: Invoicing via Partner PA (Months 7–8, before 1 Sept 2027)

- [ ] Contact 3 PAs for partner-programme terms and pricing
- [ ] Invoice model: immutable, numbering, credit notes
- [ ] Configurable VAT mention; re-check 2027 wording
- [ ] Factur-X generation
- [ ] `PlatformAdapter` + first adapter, contract tests
- [ ] E-reporting hooks
- [ ] "Mark as paid" status (no POS features); ask accountant about NF525
- [ ] vat_summary: récapitulatif TVA + FEC export
- [ ] Accountant review of invoice template
- [ ] Marketing claim only after a live adapter works

## Phase 4: Operations (Months 9–11)

- [ ] Projects, tasks, time tracking, calendar, files

## Phase 5: Commerce + RGPD (Months 10–12)

- [ ] Catalogue, orders, inventory, subscriptions, Stripe Connect Standard
- [ ] RGPD module: records, DSR tracker, retention helper, DPA generator ("aide à la conformité")

## Phase 6: Products (Months 9–14+)

- [ ] Customer Portal standalone (Month 9)
- [ ] Link in Bio: terms, abuse report, takedown, paid-first (Month 10)
- [ ] RGPD Compliance Tool standalone (Month 11)
- [ ] Community Edition, AGPL (Month 12)
- [ ] Auth / Audit / Notification APIs (Month 14+)
- [ ] Managed boilerplate hosting (Month 14+)

## Phase 6b: UK Launch (Months 12–13, only after France traction)

- [ ] Go/no-go: 20+ paying French customers, invoicing stable
- [ ] UK accountant session (VAT, invoice mentions, sole trader vs Ltd variants)
- [ ] `gb` country pack: rates, VAT-number and Companies House validators, invoice mentions, numbering
- [ ] UK legal templates (terms, DPA, privacy) and UK GDPR position confirmed (see LEGAL.md Gate 5)
- [ ] GBP pricing, en-GB copy, UK landing page, native English review
- [ ] Peppol adapter design ready (UK B2B e-invoicing mandate, April 2029)
- [ ] Stripe Connect coverage check for UK tenants

## Phase 7: Expansion

- [ ] Only if customers pull: verticals, native app, email marketing, status page

## Business Milestones

- [ ] First boilerplate sale
- [ ] First paying SaaS customer
- [ ] Month 6: accountant meeting #1 and EURL/SASU decision
- [ ] Lawyer review of CGV + DPA after first revenue
- [ ] Before Sept 2027: own invoicing PA-ready and SaaS invoicing live
- [ ] 1,000 € MRR; 5,000 € MRR (watch ceilings)

## Metrics

Signups, trial-to-paid %, MRR, churn, support hours per week, test coverage, CI duration, boilerplate sales per month.

## Open Questions

- NF525 and "mark as paid" for tenants with B2C customers (accountant)
- 2027 wording of the VAT-franchise mention
- PA partner-programme terms
- Paddle vs Lemon Squeezy / Stripe Managed Payments
- BIC vs BNC

## Decisions Log

| Date | Decision |
|---|---|
| 2026-11-18 | Global-ready architecture (country packs, i18n, multi-currency). Markets: France first, UK second (Months 12–13, after France traction), others on pull |
| 2026-11-18 | Legal-minimum plan: invoicing via partner PA; B2B only; Phase 3 split; EURL/SASU decision by Month 6; MoR for boilerplate; APIs and hosting deferred |

## Session Log

| Date | Done | Next |
|---|---|---|
| 2026-11-18 | cookiecutter-django skeleton (Python 3.14, Django 6.0, package `apps`); ruff/djlint swapped for black, isort, flake8; Makefile with `make check`; per-layer coverage gates; pre-commit; GitHub Actions CI (not yet run: no remote) | Claude Code guardrails item: `.importlinter`, day-one verification (ENFORCEMENT §9) |
| 2026-11-18 | Early decisions applied: ATOMIC_REQUESTS off; `users` app renamed `accounts`; Bootstrap/crispy replaced by Tailwind (django-tailwind-cli, Tailwind 4.3.4 pinned), shared partials for fields, messages, buttons; WhiteNoise off in tests | Claude Code guardrails item; user to log decisions (allauth MFA, Tailwind CLI) in Decisions Log and ARCHITECTURE §2 |
| 2026-11-18 | Guardrails: `.importlinter` (feature independence + layers, probed with a deliberate violation). Day-one checks: migration edit blocked ✅, .env read denied ✅, git push denied ✅, format hook ❌ (black not on PATH), Stop hook not wired (user decision) | User fixes format.py and wires Stop hook, then tick the guardrails box; next: Waitlist landing page / Phase 1 W1 core |
| 2026-11-18 | Guardrails re-verified live in a fresh session: guard_paths blocks `.claude/hooks/` write ✅, format hook reformats .py via uv ✅, stop_check fails `make check` on a probe type error ✅ and passes on a clean tree ✅; `make check` green. Guardrails box ticked | Waitlist landing page (plan + approval first) |
| 2026-11-18 | Waitlist landing page: `apps.marketing` (JoinWaitlist + SubscribeToWaitlist services, Brevo double opt-in adapter, Celery task with retry on transient errors, django-ratelimit per IP, honeypot); two-product landing at `home`; stub legal notice + privacy pages linked in footer; `WAITLIST_ENABLED` off by default; fr translations complete; exercised over HTTP (closed + open, form → redirect → task). Visual browser check not done (Chrome extension unavailable) | User: fill legal placeholders, create Brevo lists + DOI template, set env, then flip `WAITLIST_ENABLED`; next dev item: Phase 1 W1 core |
| 2026-11-18 | UX pass (outside the checklist): password show/hide toggle (Alpine CSP 3.17.5 vendored, Lucide icons); EN/FR language switcher (browser language default, cookie override); sign-up closed by default (open locally) with a waitlist-pointing closed page; email verification and sign-in by code with resend/change; one password field; no "Remember me"; no placeholders; rewritten auth templates and glossary in `locale/README.md`; friendly 429 page; redundant allauth flash messages silenced. Flows run end to end against the app; visual check still to do by the user | Phase 1 W1 core. Reminder: About page content still to write |
| 2026-11-18 | W1 core: `apps.core` with abstract models (UUIDv7 PK, TimeStamped, SoftDelete, CreatedBy, Ordered), `Money` (Decimal-only, currency-checked, half-up rounding to minor unit), injectable `Clock`, `EventBus` (on_commit, robust, idempotent subscribe). User decisions: no TenantScoped (schemas isolate tenants); Audit/Search/Notification/Export mixins built with their own apps (W6, 3a, W5, 3a). Import contract "core imports no feature app"; mypy strict on core | W1 i18n. User may want to amend ARCHITECTURE §5 for the two decisions |

## Session Starter Prompt

```
Read ARCHITECTURE.md, PRODUCTS.md, PROGRESS.md and LEGAL.md.
Continue with the first unchecked item. Write tests first. Run full CI.
Update this file and the session log before ending.
```
