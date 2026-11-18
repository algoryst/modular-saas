# PRODUCTS.md
# Product Suite from One Codebase
# Version 3 (legal-minimum plan), 18 November 2026

Prices and revenue are planning assumptions, not forecasts. Legal path per product: LEGAL.md.

---

## 1. Positioning

Horizontal platform for French SMEs (TPE/PME) with three modules plus an RGPD module. B2B only. No industry verticals unless customers pull. Sold asynchronously: email, SEO, developer communities, accounting-firm partnerships. Responsive web, no native app in v1.

- Module 1: CRM and Sales (contacts, deals, quotes, **e-signature on quotes**, invoicing via partner PA in Phase 3b)
- Module 2: Operations (projects, tasks, time tracking, calendar)
- Module 3: Commerce (catalogue, orders, inventory, subscriptions)
- RGPD compliance module (aide à la conformité)

## 1b. Markets

**France first, United Kingdom second, rest of the world only on customer pull.** The platform is built global-ready (English source strings, multi-currency, country packs: see ARCHITECTURE.md §2b). Pitch: "for freelancers and small businesses, with local compliance built in". France is the launch beachhead where compliance is the edge. The UK follows once France has paying customers and the invoicing module is stable.

| Market | Language / currency | Entry point | Notes |
|---|---|---|---|
| France | fr, EUR | Phase 3a/3b (accounting-firm partnerships, SEO) | PA-connected invoicing from Sept 2027 |
| UK | en-GB, GBP | After France (see timeline) | B2B e-invoicing mandate planned April 2029 (Peppol) ✅; UK pack before then |
| Boilerplate, Link in Bio, Portal | en + fr, USD/EUR | Global from day one | Country-neutral; sold through a merchant of record |

Competition note: outside France you compete on simplicity, price and the combined portal/Link in Bio/boilerplate offer, not on compliance. Test with an English landing page before spending build time.

## 2. The Eight Products

| # | Product | Buyer | Price (assumption) | Ships | Legal gate |
|---|---|---|---|---|---|
| 1 | **SaaS Platform** | French SMEs | 29 / 79 / 149 € per month per workspace | CRM Month 5, invoicing Months 7–8 | Gate 2, 3 |
| 2 | **Django Boilerplate** | Developers, agencies | 199–499 € one-time (via merchant of record) | Week 8 | Gate 1 |
| 2b | Managed hosting of the boilerplate | Agencies | 49–99 € per month | Month 14+ | Gate 4 |
| 3 | **API products**: Auth, Audit Log, Notification | Developers | Usage-based, from 19 € per month | Month 14+ | Gate 4 |
| 4 | **Customer Portal** (standalone) | Freelancers, agencies | 15–39 € per month | Month 9 | Gate 2 |
| 5 | **Link in Bio** (freemium funnel) | Freelancers, creators | Paid-first with trial; free tier later | Month 10 | Gate 4 |
| 6 | **RGPD Compliance Tool** (standalone) | SMEs, freelancers | 19–49 € per month | Month 11 | Gate 4 |
| 7 | **Open Source Community Edition** | Developers | Free (AGPL core); funnels to hosted | Month 12 | Gate 4 |
| 8 | **Implementation Services** | SMEs, agencies | 400–600 € per day, fixed-price scoping | From Month 5 | Gate 2 |

Ladder: Link in Bio (entry) → Customer Portal → full SaaS. The boilerplate funds the first months. The Community Edition feeds credibility and SEO.

### Changes from v2 (legal-minimum)

- Invoicing split into Phase 3b and delivered by connecting to a partner plateforme agréée. Marketing says "connecté à une plateforme agréée", never "Factur-X ready" alone.
- Partner commissions replaced by a free partner account or discount (no payment flows to third parties).
- Auth and Audit APIs and managed hosting pushed later (they mean processing other people's end-user data at scale).
- Link in Bio launches paid-first until moderation exists.
- RGPD tool wording: "aide à la conformité".
- No POS or cash-register features.
- Medical vertical stays shelved (health-data hosting rules).

## 3. Shelf (not now)

Industry verticals (only if customers pull), standalone e-signature, form builder, Django dashboard product, email marketing, status page, native mobile app, point-of-sale.

## 4. Non-Negotiables

1. Tests for every line; CI green before merge.
2. One codebase; products are app compositions.
3. B2B only; SIRET at signup.
4. We never hold customer funds.
5. We claim only what exists (compliance, signature level).
6. No cookie banner on our own site (cookieless, CNIL-exempt analytics).
7. Money in Decimal; invoices immutable.

## 5. Monthly Costs (EUR, assumptions)

| Item | Early | Mid | Scaled |
|---|---|---|---|
| Claude Code subscription | 100 | 100 | 200 |
| Scaleway hosting + backups | 20 | 50 | 120 |
| Domains, email, monitoring | 7 | 27 | 60 |
| **Total** | **~127** | **~177** | **~290** |

One-off: micro-entreprise registration free; one accountant session and one lawyer review (a few hundred euros, unverified). About 1,500 € of capital covers the first year. Merchant of record fee about 5% + 50¢ per boilerplate sale; Stripe fees on subscriptions.

## 6. Conservative Revenue Timeline (assumption)

| Month | Source | MRR / cash |
|---|---|---|
| 2 | Boilerplate launch | 1–3 sales, ~600 € one-off |
| 5 | SaaS launch | ~5 customers, ~300 € MRR |
| 7–9 | Invoicing + portal | 20–40 customers, 1,500–3,000 € MRR |
| 9–12 | Side products + services | 4,000–8,000 € MRR |

**Threshold alert:** 8,000 € MRR ≈ 96,000 € per year, above the 83,600 € micro-entreprise services ceiling. Decide on EURL/SASU **by Month 6**. The 37,500 € VAT-franchise threshold is crossed earlier: charge 20% TVA from then.

## 7. Build and Sell Timeline

| Month | Build | Sell |
|---|---|---|
| 0 | Phase 0 (legal minimum, repo, CI) | Waitlist page |
| 1–2 | Foundation, boilerplate | **Boilerplate (Week 8)** |
| 3–5 | Phase 3a CRM, quotes, e-signature | **SaaS beta, launch Month 5** |
| 6 | Structure decision (EURL/SASU), accountant meeting | Cabinet-comptable email outreach |
| 7–8 | Phase 3b invoicing via PA | Invoicing add-on before Sept 2027 |
| 9 | Customer Portal | Portal |
| 10–11 | Link in Bio, RGPD tool | Funnel + RGPD |
| 12 | Community Edition | Open source launch |
| 12–13 | **UK pack** (gb country pack, UK legal templates, GBP, en-GB copy) | **UK launch**: only if France shows traction (target: 20+ paying customers) |
| 14+ | Operations and Commerce depth, APIs | API products |

## 8. Channels

1. Email partnerships with accounting firms (they recommend tools to clients).
2. SEO in French: devis, facture électronique, RGPD pour TPE.
3. Developer communities and Product Hunt for the boilerplate.
4. Link in Bio as a viral funnel (footer attribution).
5. Open source repo and docs.

Cold email to professionals: follow LEGAL.md (identify yourself, opt-out, suppression list; confirm before mass sends).
