# FABIABox Marketing Site — Design Context

Running domain/decision log for the `fabia_web` project.

## Terminology

| Term | Definition |
|------|------------|
| **FABIABox** | Public-facing product brand: a sovereign AI workstation for non-technical entrepreneurs. Spin-off from SquadShelf / IABAI Research. |
| **Fabia** | The AI Architect inside FABIABox. Receives the user's idea/documents, orchestrates agents, refines the plan, and runs autonomous execution after approval. |
| **SquadShelf** | Parent/origin concept; currently redirects to fabiabox.com. Also an agentic-services marketplace layer. |
| **Lead** | A visitor who submits name/email/message via the landing page form. |
| **Landing Page** | Single-page static site (`index.html`) served at `fabiabox.com`. |
| **Contact CSV** | `data/contacts.csv` — local source of truth for lead storage. |
| **Deploy Script** | `deploy.sh` — pushes whitelisted files to DO droplet and syncs contacts back. |
| **FABIABox Pipeline** | End-to-end workflow: idea intake → analysis/refinement → business plan → approval → build → launch → operate → optimize. |
| **Agent Roles** | Specialist fine-tuned models acting as Market Researcher, Business Manager/CEO, Coder, QA, Security, DevOps/Infrastructure, Marketer, KPI/CEO. |
| **RACI Matrix** | User-configurable responsibility matrix defining which decisions are automated vs. require human approval. |
| **Legal Signature Gate** | Any step requiring legal signature pauses autonomous execution and engages the user for explicit approval. |
| **Ecosystem Tools** | External/related IABAI tools: IntentRanker, IAB.AI, Docostream, SquadSign. |

## Design Decisions

| ID | Decision | Rationale | Open Questions |
|----|----------|-----------|----------------|
| D1 | Static HTML landing page + Flask micro-backend | Simple, cheap, fast to iterate; only dynamic need is lead capture. | When do we outgrow this and move to a framework/build step? |
| D2 | Contacts stored in CSV on droplet, synced locally | Zero external dependencies; easy to inspect/backup. | GDPR/data-retention policy? Export to CRM pipeline? |
| D3 | nginx reverse-proxy to Flask on loopback (`127.0.0.1:8080`) | Decouples static file serving from dynamic API. | HTTPS/certbot now included in `nginx.conf` via remote commits (c5f9a21, 9db68cd); deploy script refuses HTTP-only configs (d9c8c01). |
| D4 | Whitelist-based file serving in Flask (`SERVABLE`) | Prevents accidental leakage of `.env`, `.git`, source files. | nginx already blocks some extensions; is the Flask whitelist redundant or complementary? |
| D5 | Deploy via base64-over-SSH instead of SCP/RSYNC | Avoids SCP/RSYNC port/firewall issues. | Remote commit d9c8c01 added safety guard: refuses to deploy HTTP-only nginx config. |
| D12 | Launch date is Q3 2026 | Updated from Q2 2026 to match product roadmap. | Ensure all deck materials and socials are aligned. |
| D13 | Founder experience framing | 27 years of IT experience across several fields including automation and AI; IABAI SaS exists for 4 years and holds the French CII agreement. | Add CII agreement badge/reference if available. |
| D14 | Tri-silicon hardware strategy | NVIDIA Thor + AMD Ryzen AI Max+ + NVIDIA DGX Spark (1 PFlop Pro tier); enterprise DGX (20 PFlop) on roadmap. | Update technical architecture deck accordingly. |
| D15 | Connectivity modes | FABIABox supports Local network, Internet, and Air gap operation. | Add to spec sheet and privacy/security messaging. |
| D6 | Financial model CSV is **not** publicly served | Exact-match nginx location outranked regex deny rule, accidentally exposing the CSV. Removed exact-match block; regex deny now applies. | Keep PDF summary as public investor material. |
| D7 | Lead follow-up is async via cron + Telegram | User already has a cron job that polls/syncs leads and sends Telegram notifications. No real-time email/CRM needed at this stage. | Document cron command and notification format in CONTEXT.md. |
| D8 | GDPR: privacy policy + consent checkbox | Site collects EU visitor data; add `/privacy.html` and require explicit consent before form submission. | Review retention period (set to 24 months in policy) and provide data-deletion process. |
| D9 | FABIABox is the execution pipeline; ecosystem is separate but supporting | Landing page must clearly distinguish the in-the-box workflow from external ecosystem tools. | ✓ Add "How FABIABox Works" 6-stage section; keep ecosystem map with status badges. |
| D10 | Role-based autonomy with user-configurable RACI | User can be fully hands-off, step in as any C-suite role, or act only as President/Owner. Legal signatures always require user. First-run wizard sets the level; out of scope for marketing site. | First-run wizard UX design belongs in product repo, not fabia_web. |
| D11 | Investor deck is delivered manually after form submit | Form sets expectation of email follow-up; executive summary is available instantly post-submit. | Ensure cron/Telegram loop includes deck-send reminder or auto-notify. |

## FABIABox Pipeline Flow

```
User (Telegram / WhatsApp / Email / Local Web)
    ↓
Presents idea + documents (raw or advanced)
    ↓
Fabia (AI Architect)
    ↓
├── Market Researcher agent (fine-tuned model)
└── Business Manager / CEO agent (fine-tuned model)
    ↓
Fabia asks clarifying questions; loops with user until idea is solid
    ↓
Business plan presented to user
    ↓
User approval gate
    ↓
Autonomous execution (configurable per RACI):
    ├── Build  → Coder + QA + Security agents
    ├── Launch → Deployment + Infrastructure agents
    ├── Operate → Marketing agents
    └── Improve → KPI / CEO agents
    ↓
Legal signature required → pause and engage user
    ↓
Continuous operation / optimization loop
```

## Ecosystem Map (Supporting, Not In-Box)

| Tool | Status | Role in FABIABox |
|------|--------|------------------|
| **IntentRanker** (intentranker.com) | Live | Market analysis; connects users with companies needing their services. |
| **IAB.AI** (iab.ai) | Yet to deploy | Fine-tuning engine; provides best fine-tuned models for FABIABox agents. |
| **Docostream** (docostream.com) | Yet to deploy | Document extraction / ingestion for raw idea materials. |
| **SquadSign** | Yet to deploy | Legal signature layer for agent-executed contracts. |
| **SquadShelf** (squadshelf.com) | Redirects to fabiabox.com | Agentic-services marketplace / parent brand. |

## Website Pipeline Flow

```
Visitor → fabiabox.com → nginx
                        ├── static files (index.html, PDF, PNG, privacy.html)
                        └── /submit → Flask → append to data/contacts.csv

Developer → local edit → git commit → ./deploy.sh
                                      ├── check/pull origin/main
                                      ├── transfer whitelisted files
                                      ├── update nginx config if changed
                                      ├── reload gunicorn
                                      └── pull contacts.csv locally
```

## Open Questions

1. What is the next evolution of this site? (multi-page, CMS, investor portal, docs?)
2. How should leads be actioned after capture? (email notification, CRM integration, manual review)
3. Should the financial model CSV be publicly downloadable? → **Resolved: no, blocked.**
4. HTTPS/certbot: currently HTTP-only on port 80. → **Resolved: certbot managed outside repo.**
5. nginx root path mismatch and HTTP-only config: **Resolved** by remote commits (c5f9a21, d9c8c01, 9db68cd) that consolidated nginx.conf with SSL and added a deploy safety guard. |
6. Default autonomy level for new FABIABox users: first-run wizard sets RACI; out of scope for marketing site. |
7. How prominently should ecosystem tools appear on the landing page vs. the in-the-box process?
8. Landing page should explain FABIABox process clearly and keep ecosystem map lightweight.

## Model / Tool Defaults

N/A for this static site. If agentic features are added later (e.g., AI chat, dynamic content), record fallback models and tool IDs here.

## Literature-Backed Best Practices

TBD — append if user supplies relevant references.
