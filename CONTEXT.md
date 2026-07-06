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

---

## Design Decisions

| ID | Decision | Rationale | Open Questions |
|----|----------|-----------|----------------|
| D1 | Project seeded from `fabia_web` (marketing site) and `fabia-0.3` (orchestrator) | Reuse terminology, pipeline, and decision patterns. | What exactly does `fabiaweb_shop` build? |
| D2 | `fabiaweb_shop` is a **hardware + subscription storefront** for FABIABox. Phase 1 is waitlist / pre-buy only. | Name and ecosystem context point to a shop; no third-party marketplace yet (that's a separate project); white-label checkout is interesting but not phase 1. | Which tiers/services are offered at launch? What is the difference between "pre-buy" and "waiting list"? |

---

## Pipeline Flow

*TBD — depends on what `fabiaweb_shop` becomes.*

---

## Open Questions

1. What is `fabiaweb_shop`? (marketplace, storefront, checkout, product catalog, subscription management, etc.)
2. Who is the user? (end customer, investor, admin, agent)
3. Does it integrate with the existing FABIABox pipeline, or is it a standalone surface?
4. What is the deployment target? (same nginx/Flask stack as fabia_web, or new service)

---

## Model / Tool Defaults

*TBD — record fallback models and external tool IDs as they are decided.*
