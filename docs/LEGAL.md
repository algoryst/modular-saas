# LEGAL.md
# Minimum Legal Path — Build and Sell With the Least Friction
# Checked 18 November 2026

---

## How to Read This File

- ✅ = checked against sources on 18 Nov 2026
- ⚠️ = from general knowledge, NOT verified. Confirm with your accountant or a one-hour lawyer consult before relying on it.

I am not a lawyer or an accountant. This file is a work plan, not advice.

## The Principle

Do the minimum before each *gate*, not before everything. Each gate unlocks one stage of selling.

```
Gate 1  → sell the boilerplate (Week 8)        ~1-2 days of admin
Gate 2  → launch the SaaS (Month 5)            ~1 week of admin + 1 accountant meeting
Gate 3  → ship invoicing (before 1 Sept 2027)  PA connection + template review
Gate 4  → side products (Link in Bio, APIs…)   only when each one ships
Gate 5  → UK launch (Months 12–13)             UK GDPR, UK VAT, UK templates, after France traction
```

---

## Gate 1 — Before the First Sale (Boilerplate, Week 8)

Why this is the lightest gate: buyers are developers, a merchant of record is the legal seller, and the product contains no customer data.

| # | Action | Effort | Status |
|---|--------|--------|--------|
| 1 | Register a micro-entreprise on the Guichet unique (formalites.entreprises.gouv.fr, run by INPI). Free, fully online, about 30 minutes | 1 hr | ✅ |
| 2 | Ask an accountant whether SaaS/software income is BIC or BNC for your case, and pick the activity wording accordingly | 30 min | ⚠️ |
| 3 | Open a separate bank account for the business | 1 hr | ⚠️ recommended |
| 4 | Publish **mentions légales** (LCEN art. 6-III): your name + status "Entrepreneur individuel / micro-entrepreneur", address (a domiciliation address is acceptable), phone, email, SIRET, director of publication (you), and your host's name, address and phone | 1 hr with a template | ✅ |
| 5 | Publish a **privacy policy** (you collect waitlist and customer emails) | 1 hr with a template | ⚠️ |
| 6 | Publish **licence terms / CGV** for the boilerplate (what buyers may and may not do) | 2 hrs | ⚠️ |
| 7 | **Cookies — no banner needed if** the marketing site sets only strictly necessary cookies and uses an audience-measurement tool that meets the CNIL exemption: purpose strictly limited to audience measurement for you, anonymous statistics only, no cross-referencing, no data reuse by the vendor, users informed in the privacy notice. Since 1 Jan 2026 the CNIL no longer publishes a list of exempt tools; the vendor self-assesses. Matomo documents a CNIL-exempt configuration (disable User ID, heatmaps, session recording and e-commerce tracking). Plausible: I did not verify its statement, check before using. No Google Analytics, no ad pixels, no embedded YouTube | 2 hrs | ✅ |
| 8 | Sell through a **merchant of record** (Paddle, or Lemon Squeezy / Stripe Managed Payments). The MoR is the legal seller, collects and remits EU VAT and files OSS returns. Typical fee about 5% + 50¢ per sale. Lemon Squeezy announced Stripe Managed Payments in Jan 2026 and one source questions its future, so compare both at launch | 2 hrs | ✅ |
| 9 | Keep a one-page **RGPD register** (spreadsheet): tab 1 = your own processing as controller (waitlist, accounts, billing); tab 2 = list of sub-processors (Scaleway, Brevo, Stripe, Sentry, MoR) | 1 hr | ✅ |
| 10 | If you send **cold email to professionals** (accountants, federations): ⚠️ B2B prospecting to a professional address is generally allowed when the offer relates to their profession, if you identify yourself, give an easy opt-out, and keep a suppression list. Confirm before a mass send | 1 hr | ⚠️ |

**Not needed at Gate 1:** lawyer review, DPA, PA connection, EURL/SASU, insurance, trademark.

### Your own invoices — the franchise en base mention ✅

- While you are in VAT franchise, every invoice must say: **« TVA non applicable, art. 293 B du CGI »**. "Sans TVA" or "TVA 0 %" is not compliant.
- One source says this wording stays valid until 31 Dec 2026; another notes the mention evolves with the recodification of the tax code. **Store the mention as a configurable field and re-check the wording for 2027.**
- Franchise thresholds 2026 (services): **37,500 €** (majoré 41,250 €). The 2026 franchise is judged on your 2025 revenue. The government dropped the reform of these thresholds at the end of 2025.
- Micro-entreprise revenue ceilings 2026-2028: **83,600 €** services, **203,100 €** sales.

### Your own e-invoicing — do not forget yourself ⚠️

Reception of e-invoices has been mandatory for VAT-liable businesses since 1 Sept 2026 ✅. Issuing e-invoices becomes mandatory for small businesses on 1 Sept 2027 ✅. From then, **your own B2B invoices to French customers may need to go through a plateforme agréée**, and Stripe invoices alone may not be enough. Ask your accountant whether franchise en base changes this for you. The simple fix: invoice with a PA-registered tool. Several advertise free plans (Indy, Tiime, Abby): verify the terms.

---

## Gate 2 — Before the SaaS Launch (Month 5)

| # | Action | Status |
|---|--------|--------|
| 1 | **DPA (RGPD art. 28(3))** as an annex to your CGU. As a SaaS publisher you are the *processor* for what the tenant does in the product; you stay *controller* for your own accounts and billing data (CNIL cloud-actor guidance, 28 May 2026, via secondary source) | ✅ |
| 2 | **Processor register (art. 30(2))**: processing is not occasional for a SaaS, so assume you need it. Extend the Gate 1 spreadsheet with one entry per processing activity | ✅ |
| 3 | **Public sub-processor list** (Scaleway, Brevo, Stripe, Sentry in an EU region ⚠️) and a change-notification promise | ✅ |
| 4 | **B2B-only CGV**: SIRET required at signup. Avoids consumer-law duties (withdrawal right, mediation) | ⚠️ |
| 5 | **Stripe** for your subscriptions. For tenants collecting from their own clients, use **Stripe Connect Standard** (funds go straight to the tenant's Stripe account, you never hold money, no platform fee in v1). Confirm in Stripe's docs | ⚠️ |
| 6 | **Accountant meeting #1 (about 1 hr)**: BIC/BNC, thresholds, your own e-invoicing, MoR payout bookkeeping, when to move to EURL/SASU | ⚠️ |
| 7 | **Lawyer review (about 1 hr)** of CGV + DPA. Can happen right after your first revenue | ⚠️ |
| 8 | **Marketing claims rule**: do not say "conforme facture électronique" until the PA connection works. Say "préparé" or "Factur-X" only for what exists | ✅ |
| 9 | **E-signature**: market only "signature électronique simple" (eIDAS simple). Never "qualifiée" or "avancée" | ⚠️ |
| 10 | **RGPD tool wording**: "aide à la conformité", templates with disclaimers. Never "garantit la conformité" | ⚠️ |
| 11 | Breach procedure (one page): detect, tell affected tenants without undue delay, log it | ⚠️ |

---

## Gate 3 — Before Invoicing Ships (Phase 3b, before 1 Sept 2027)

| # | Action | Status |
|---|--------|--------|
| 1 | **Do not become a PA.** Registration is a full audit by the DGFiP, too heavy for a solo developer. Connect to a PA as a "solution compatible" (for example Pennylane lists 120+ publishers). Programme terms and pricing: not verified, contact 3 PAs early | ✅ / ⚠️ |
| 2 | Factur-X, UBL and CII are the three accepted formats ✅. Factur-X alone does not make you compliant: only a registered PA handles transmission and e-reporting ✅ | ✅ |
| 3 | **Accountant review of the invoice template** once: mandatory mentions, gap-free numbering, credit notes | ⚠️ |
| 4 | **Invoices are immutable once issued**; corrections go through credit notes | ✅ (general invoicing rules) |
| 5 | **Retention**: invoices typically kept 10 years. Conflicts with RGPD erasure: design for anonymising personal fields while keeping the document | ⚠️ |
| 6 | **NF525 / anti-fraud**: applies to VAT-liable businesses that record payments from *private individuals* in a software or cash system; invoicing software without payment-collection function is not in scope; only the payment-recording part of a broader tool needs certification; franchise en base is out of scope ✅. **Open question:** would the "mark invoice as paid (cash, cheque, transfer)" feature put a tenant in scope? Mitigation: B2B only, "marquer comme payée" status without till-style features, and ask your accountant | ✅ / ⚠️ |

---

## Gate 4 — Before Each Side Product

| Product | Extra legal step |
|---------|------------------|
| Customer Portal standalone | Same as SaaS: B2B terms, DPA, Stripe Connect |
| Link in Bio | ⚠️ You host user-generated public pages: terms of use, abuse-report link, takedown procedure, verified email at signup. Recommended: launch paid with trial first, add a free tier once moderation exists |
| RGPD tool standalone | Disclaimers. No legal-advice positioning |
| Managed hosting | You process buyers' end-user data: needs the DPA and processes proven first. Defer |
| Auth / Audit / Notification APIs | You process third parties' end-user data at scale: DPA, security documentation, uptime commitments. Defer to Month 14+ |
| Medical or other regulated verticals | Out of scope (health data hosting rules). Stay shelved |
| Point-of-sale features | Do not build (certification burden) |

---

## Gate 5 — Before the UK Launch (Months 12–13)

Do this only after France shows traction. France remains the priority; nothing here blocks the French launch.

| # | Action | Status |
|---|--------|--------|
| 1 | **UK e-invoicing**: the UK has confirmed mandatory B2B e-invoicing from **April 2029**, based on Peppol. No need to build before then; keep the adapter interface ready | ✅ (multiple sources; exact scope details not read) |
| 2 | **UK GDPR + Data Protection Act 2018**: you will process UK customers' data, so UK GDPR applies alongside EU GDPR. Check whether you need to pay the ICO data protection fee or appoint a UK representative (ICO guidance exists on both; I did not read the detail) | ⚠️ |
| 3 | **Data transfers**: UK customers' data hosted in the EU, and EU data going to the UK. Confirm the current adequacy position and that your DPA covers UK GDPR (a UK addendum is common) | ⚠️ |
| 4 | **UK VAT**: from your side, selling a subscription to UK businesses is generally an overseas B2B supply; the exact rules for a French entity selling to UK customers (and whether a UK VAT registration is needed) must be confirmed with an accountant. Easiest path: use the merchant-of-record route for UK sales until revenue justifies a check | ⚠️ |
| 5 | **Tenant-side UK invoicing**: UK VAT-registered tenants need a VAT number and standard mentions on invoices; non-VAT-registered sole traders use a simpler invoice. Review the `gb` pack template with a UK accountant. UK VAT registration threshold (I recall £90,000): verify | ⚠️ |
| 6 | **UK consumer vs B2B**: keep B2B only (company or sole trader with business purpose), as in France | ⚠️ |
| 7 | **UK legal templates** (terms, privacy, DPA): lawyer review once, after first UK revenue | ⚠️ |
| 8 | **Currency and payouts**: GBP Stripe account/payout handling and bookkeeping of GBP income in your French books: add to the accountant questions | ⚠️ |

---

## What Can Wait

- Lawyer review (until first revenue)
- PA connection (until Phase 3b)
- EURL/SASU switch (until the thresholds below approach)
- Professional liability insurance: recommended, not mandatory for most; revisit at launch ⚠️
- Trademark filing (do a free INPI name search before buying the domain)
- DPO appointment, formal security certification

---

## Business Structure and Thresholds

- Crossing the **VAT threshold** (37,500 €) simply means you start charging 20% TVA; B2B customers recover it. Build the product and your own invoicing to handle both states.
- The real forcing function is the **83,600 € micro-entreprise ceiling**. If your revenue plan lands near 8,000 €/month by Month 9, you would pass it within a year of selling. **Decide on EURL/SASU by Month 6**, not after.

---

## Open Questions for the Accountant (bring this list)

1. BIC or BNC for SaaS + boilerplate income?
2. Am I covered by e-invoicing issuance/reception duties from Sept 2026/2027 while in franchise?
3. How do I book MoR payouts (Paddle / Lemon Squeezy) in my accounts?
4. When should I move to EURL or SASU, and what does it cost to move?
5. Does a "mark as paid" feature put my tenants in NF525 scope?
6. Retention period for invoices and what happens to personal data inside them?
7. Cold email to professionals: any extra rules for my case?
8. (Before UK launch) VAT treatment of selling subscriptions to UK businesses from a French entity, and bookkeeping of GBP income?
9. (Before UK launch) ICO fee, UK representative, and UK GDPR transfer position for my setup?

## Legal Budget

Almost all of Gate 1 is free or a few hours of your time. Budget a few hundred euros for one accountant session and one lawyer review around launch. I did not verify current rates.

---

*Last checked: 18 November 2026*
