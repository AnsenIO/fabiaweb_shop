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

---

## Pipeline Flow

*TBD — depends on what `fabiaweb_shop` becomes.*

---

## Open Questions

1. What form fields are captured for pre-buy / waitlist?
2. Where is order data stored?
3. How are pre-buy / waitlist submissions notified to the team?
4. What is the pricing / deposit structure for each SKU?
5. What is the deployment target? (same nginx/Flask stack as `fabia_web`, or new service)
6. Does `fabiaweb_shop` integrate with the existing FABIABox pipeline, or is it a standalone surface?

---

## Model / Tool Defaults

*TBD — record fallback models and external tool IDs as they are decided.*
