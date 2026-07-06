# fabiaweb_shop — Domain Glossary & Design Log

> Running source of truth for the `fabiaweb_shop` project. Seeded from `fabia_web` and `fabia-0.3`; revised during grilling.

---

## Terminology

| Term | Definition | Source |
|------|------------|--------|
| **FABIABox** | Sovereign AI workstation / "system in a box" for non-technical entrepreneurs. | fabia_web |
| **Fabia / Architect** | Primary AI agent that faces the user and orchestrates the idea-to-product pipeline. | fabia-0.3 |
| **Pipeline** | Internal sequence of stages: idea → ingestion → market research → PRD → feature mapping → coding → testing → QA → deploy. | fabia-0.3 |
| **Sub-Agent** | Specialist agent (Market Analyst, PRD Generator, Feature Mapper, Coding Agent, etc.). | fabia-0.3 |
| **Approval Gate** | Checkpoint where the Architect pauses for human validation before continuing. | fabia-0.3 |
| **Artifact** | Structured output of a pipeline stage (dossier, PRD, task mapping, code). | fabia-0.3 |
| **SquadShelf** | Model/prompt library and parent brand; currently redirects to fabiabox.com. | fabia_web |
| **fabiaweb_shop** | *TBD — this project.* To be defined during grilling. | — |

## Catalog (Phase 1)

All SKUs priced in **EUR** and offer either **Pre-buy** or **Waiting list**.

| # | SKU | Category | Silicon / Description | Phase 1 action |
|---|-----|----------|-----------------------|----------------|
| 1 | **FABIABox Entry** | Hardware | AMD Ryzen AI Max+ | Pre-buy or waiting list |
| 2 | **FABIABox Edge** | Hardware | NVIDIA Thor | Pre-buy or waiting list |
| 3 | **FABIABox Pro** | Hardware | NVIDIA DGX Spark (1 PFlop) | Pre-buy or waiting list |
| 4 | **FABIABox Enterprise** | Hardware | NVIDIA DGX roadmap (20 PFlop) | Pre-buy or waiting list |
| 5 | **Agentic Build Plan** | Service subscription | Annual plan — build/launch phase | Pre-buy or waiting list |
| 6 | **Agentic Operate Plan** | Service subscription | Annual plan — operate/optimize phase | Pre-buy or waiting list |

---

## Design Decisions

| ID | Decision | Rationale | Open Questions |
|----|----------|-----------|----------------|
| D1 | Project seeded from `fabia_web` (marketing site) and `fabia-0.3` (orchestrator) | Reuse terminology, pipeline, and decision patterns. | What exactly does `fabiaweb_shop` build? |
| D2 | `fabiaweb_shop` is a **hardware + subscription storefront** for FABIABox. Phase 1 is waitlist / pre-buy only. | Name and ecosystem context point to a shop; no third-party marketplace yet (that's a separate project); white-label checkout is interesting but not phase 1. | Which tiers/services are offered at launch? |
| D3 | Launch catalog = **6 SKUs**, currency **EUR**. Every SKU offers either **pre-buy** (pay now) or **waiting list** (no payment). | Confirmed by user. Pre-buy = priority fulfillment; waitlist = expression of interest. | What is the pricing / deposit structure for each SKU? |
| D4 | **No automated checkout in Phase 1.** Pre-buy and waitlist both use the same form; pre-buyers are invoiced manually afterwards. | Keeps the site static, avoids PCI/integration complexity, matches `fabia_web` lead-capture pattern. | What form fields are captured? Where is the data stored? How are notifications handled? |
| D5 | Order form captures: **name, email, company, country, SKU, quantity, action (pre-buy/waitlist), message**; stored in `data/orders.csv` with `status` column. | Confirmed by user. GDPR consent checkbox + privacy policy link required (24-month retention). | Where is the site deployed? How are submissions notified? |
| D6 | Deploy at **`shop.fabiabox.com`** on the same droplet as `fabiabox.com`, but as a **separate repo/project** with its own `deploy.sh` and `data/orders.csv`. | Clean separation while sharing operational overhead; matches user preference for different repo. | How are order submissions notified? What is the pricing/deposit structure? |
| D7 | Order notifications use **cron + CSV sync + Telegram**, same pattern as `fabia_web` lead notifications. | Offline, reliable, no real-time integration complexity in Phase 1. | What is the pricing/deposit structure for each SKU? |
| D8 | **Pricing display:** services show a monthly EUR fee; hardware shows "Price on request" (placeholders for Phase 1). | Services are easier to price upfront; hardware costs fluctuate. | What are the placeholder monthly prices for Build/Operate plans? Should hardware show a pre-buy deposit amount or just "Price on request"? |
| D9 | **Service pricing:** Build Plan = **€49.99/month**, Operate Plan = **€49.99/month**, annual plan = **€499**. Hardware shows a **pre-buy reservation**. | Confirmed by user. Annual plan is roughly 2 months free vs monthly. | What is the hardware pre-buy reservation amount? Should it be a fixed deposit or "Contact us"? |
| D10 | **Hardware pre-buy reservation = €500** per unit. Displayed as "Pre-buy reservation: €500" (refundable / credited toward final invoice). | Confirmed by user. Filters serious buyers without being prohibitive. | What happens after form submission? Does the shop connect to the FABIABox pipeline or stay standalone? |
| D11 | **Post-submission = simple thank-you page.** `fabiaweb_shop` is **standalone** in Phase 1; no automatic handoff to `fabia-0.3` pipeline. | Marketing site should not depend on an unfinished orchestrator. Manual follow-up from CSV. | What tech stack and deployment structure do we use? |
| D12 | **Tech stack mirrors `fabia_web`:** static HTML, Flask loopback API, nginx reverse proxy, base64-over-SSH deploy, cron+Telegram notifications. | Proven, cheap, fast to iterate; keeps operational overhead identical. | Start implementation now or refine further? |

---

## Pipeline Flow

```
Visitor → shop.fabiabox.com → nginx
                            ├── static files (index.html, PDF, PNG, privacy.html)
                            └── /submit → Flask → append to data/orders.csv

Developer → local edit → git commit → ./deploy.sh
                                          ├── check/pull origin/main
                                          ├── transfer whitelisted files
                                          ├── update nginx config if changed
                                          ├── reload gunicorn
                                          └── pull orders.csv locally

Cron → fetch-orders.sh → sync orders.csv → Telegram notification for new entries
```

## Open Questions

1. Start implementation now, or refine design further?
2. Should the site include a privacy policy specific to `shop.fabiabox.com` or reuse `fabiabox.com/privacy.html`?
3. Should `fabiaweb_shop` link back to `fabiabox.com` research/investor pages?

---

## Model / Tool Defaults

*TBD — record fallback models and external tool IDs as they are decided.*
