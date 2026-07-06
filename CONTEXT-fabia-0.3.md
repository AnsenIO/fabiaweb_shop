# CONTEXT.md — FABIA Domain Glossary

> **Purpose:** Ubiquitous language for the FABIA system. Updated during grilling sessions.
> **Last updated:** 2026-06-30

---

## Core Concepts

### Architect (FABIA)
The primary agent that faces the user. It is the pipeline personified — the "business architect" that manages the entire idea-to-profit lifecycle autonomously. It manages a team of specialized sub-agents and (eventually) humans.

### Pipeline
The internal business process: idea → document ingestion → market research → PRD → feature mapping → coding → testing → deployment. It is the *mechanism* by which the Architect delivers value. The user never sees the pipeline directly.

### Uploaded Document
A user-provided file (`.md`, `.txt`, or `.pdf`) submitted alongside an idea or during any pipeline stage. Extracted text is injected into agent prompts and originals are stored in `storage/projects/<slug>/uploads/`.

### Black Box
The user-facing property of FABIA. The user only interacts through interfaces (Telegram, WhatsApp, email, web). They provide an idea and receive results — they do not see or control the internal pipeline stages.

### Business Factory
The GB10-hosted infrastructure where the pipeline executes. It contains multiple models, agents, prompts, and hardware resources. The factory is the *means*; the Architect is the *manager*.

### Neo-Entrepreneur
The target user. Non-technical. Provides raw ideas; expects business value (profit) as output. Does not need to understand how the pipeline works.

### Interface
Any channel through which the user communicates with the Architect: Telegram, WhatsApp, email, web (Flask admin). Each interface delivers the same pipeline experience.

### Artifact
A structured output produced by a pipeline stage. Examples: `market_research_dossier`, `prd_dossier`, `task_mapping`, `code_artifacts`. Artifacts flow between stages and are validated at approval gates. Uploaded documents are also treated as artifacts after ingestion.

### Uploaded Document Artifact
The structured record produced by Document Ingestion for each uploaded file: original path, extracted text path, word count, and MIME type. Stored per project in `storage/projects/<slug>/uploads/`.

### Approval Gate
A checkpoint in the pipeline where the Architect pauses and asks the user to validate an artifact. The user can approve, reject (with feedback), or request revision. Not all stages have gates — only those where human judgment adds value.

### Sub-Agent
A specialized agent that performs a single pipeline stage (Market Analyst, PRD Generator, Feature Mapper, Coding Agent, etc.). Each has its own memory space, prompt, and model assignment.

### Model Router
The component that assigns inference models to sub-agents. Routes based on task type and historical performance scoring. Supports multiple models per agent type for economic optimization.

### Memory-as-a-Tool
Per-agent persistent memory stored in `.fabia_agents/<agent>/memory_as_tool.md`. Distilled feedback from user reviews, lessons learned, and guidelines. Injected into the next invocation's context.

### FABIABox
The GB10-hosted deployment platform. Initially a managed web service (monthly fee + variable on product). Later a "system in a box" — self-hosted appliance for on-premise deployment.

### Business Value
The ultimate output of the pipeline. Not just code — a deployable product with market validation, clear requirements, and tested code. The Architect's job is to deliver profit-ready assets.

---

## Terminology Decisions

| Term | Definition | Why |
|------|------------|-----|
| **Architect** (not "Orchestrator") | The primary FABIA agent facing the user | "Orchestrator" is an implementation detail. "Architect" is the domain role. |
| **Pipeline** (not "workflow" or "process") | The internal sequence of stages | "Pipeline" conveys the idea-to-product flow. |
| **Black Box** | User-facing abstraction | Emphasizes that users interact only through interfaces, not internals. |
| **Artifact** (not "output" or "document") | Structured pipeline output | "Artifact" is the standard term for engineered outputs. |
| **Approval Gate** (not "review" or "checkpoint") | Human validation point in the pipeline | "Gate" conveys the stop/resume nature. |
| **Grill Section** | Pre-flight stress-test before market research | The Grill Architect interrogates the raw idea before any research begins. |
| **Autonomy Level** (3 or 5) | User-configurable autonomy setting | Determines how many gates the user sees vs. auto-approved stages. |
| **System in a Box** | Self-hosted FABIA appliance | Single-tenant, isolated, user-owned. Runs on GB10 with Obsidian, LMStudio, etc. |
| **Connectivity Profile** | What external services are available | Determines whether the Architect can reach Slack, Notion, Jira, etc. |
| **Vertical Development** | Features distributed into logical development stages | Not horizontal (all features at once) but vertical (one complete feature at a time). |
| **TDD Loop** | Coding agent's internal cycle: develop → sonarqube → revise → test → commit | The Coding Agent uses test-driven development with SonarQube feedback. |
| **QA Inspector** | Modular code analysis agent | Runs static analysis on each committed feature; provides feedback to the coder. |
| **Auto-Deploy** | Docker-compose deployment to local network | Initially local; later configurable for cloud/hosted deployments. |
| **Obsidian** | Document storage and sync | Initial document management; later replaced by Obsidian MCP integration. |
| **Business Plan** | Approved artifact after Grill Section | The validated business plan is the contract between user and pipeline. User takes legal ownership. |
| **Feature Request** | Approved feature specification | User-approved features that the pipeline commits to building. Extracted by a dedicated Feature Mapper agent. |
| **Commitment** | A single feature's development cycle | Includes code, tests, SonarQube analysis, and review. One feature per commit. |
| **Legal Ownership** | User takes full ownership of approved documents | The user approves documents to take legal responsibility for the business. |
| **Web Service Mode** | Managed multi-tenant FABIA | Initially offered as a web service with monthly fee + variable on product. |
| **Local Mode** | Self-hosted FABIA on user's hardware | "System in a box" — single tenant, isolated, user-owned. |
| **Feature Mapper Agent** | Dedicated agent for feature extraction | Has its own context window and fine-tuned model. Extracts features from the Business Plan. |
| **Feature Request** | Approved feature specification | User-approved features that the pipeline commits to building. |
| **Connectivity Profile** | What external services are available | Determines whether the Architect can reach Slack, Notion, Jira, etc. |
| **SonarQube** | Static analysis engine on the box | Already running on GB10. Instructions for project usage are available and will be provided to the Architect. Used by QA Inspector on each committed feature. |
| **Obsidian Vault** | Source of truth for all pipeline documents | The vault lives inside the codebase at `storage/vault/`. The pipeline reads from and writes to the vault. The user accesses it through Obsidian on the GB10 box. Later replaced by Obsidian MCP integration for real-time sync. |
| **Role-Based Approval** | Approval level defined by user role and Architect roles | The Architect takes on roles (CTO, CIO, CMO, CFO, COO) and the user takes on roles (CEO, investor/president, or contributes in specific areas like CMO/CFO). Approval gates are determined by role overlap. Later phase: RACI matrix for role fine-tuning. |
| **Project Folder Management** | Archive old project, create new | When the user decides to change ideas, the Architect archives the old project folder and creates a new one for the new project. |
| **SquadShelf** | Model and prompt library | Placeholder for now. Provides models and prompts for each agent phase. Later replaced by real model library. |
| **Model Fallback** | qwen3.6-35b-a3b (non-coding), qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled (coding) | Configured in .env (later admin interface). All models loaded through LMStudio on port 1234. Exact IDs from LMStudio: `qwen/qwen3.6-35b-a3b` and `qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled`. Also available: `google/gemma-4-12b`. |
| **Model Routing Tool** | `give-me-model-and-prompt-for(agentphase)` | Queries local SQLite, then SquadShelf, then falls back to defaults. Agent phases: market research, feature extract, prd, coding, code, deploy, operations. Returns model name + system prompt. |
| **Role Selection** | Initial interview + per-project switching | User selects roles during initial interview with FABIA. Can switch per project. Initially single-business focus per box (soft limit/recommendation). |
| **Subagent Invocation** | `invoke_subagent(agent_name, task)` | Tool to invoke any subagent at any point during the pipeline. |
| **OpenCode Execution** | `execute_opencode(task, method='tdd')` | Execute opencode for coding, applying /tdd and /opencode delegation principles. |
| **Project Naming** | FABIA creates code name with user | FABIA creates project name/code name and folder structure once it understands the idea and brainstorms with user. Code name, not brand yet. |
| **Grill Iteration** | Grill stages re-iterated after market analysis | Grill stages are done one by one as concepts improve. Initially brainstorming, then re-iterated after market analysis to validate/improve each topic. |
| **Grill Auto-Approve** | Auto-approve with autonomy, motivate with facts | If user grants autonomy, Architect auto-approves but motivates choices with facts and sources from market research. Always documents with data sources. |
| **Grill CEO Mode** | FABIA acts as CEO when autonomous | If FABIA has CEO role, all decisions are on FABIA but informs user and requests formal sign-off before business launch. |
| **invoke_subagent** | Comprehensive subagent invocation tool | Takes: agent_name, task, prompt (if None takes from give-me-model-and-prompt-for), model (if None takes from function), subproject directory, input files/subvault/subdirectory. |
| **Model Routing** | Simple external function or @tool | `give-me-model-and-prompt-for(agentphase)` can be a simple external function or @tool added to the Architect. Returns model name + system prompt. |
| **Market Research Helper** | Re-engagable helper node | Market research agent is a helper for the Architect, re-engaged anytime needed. Can loop back: architect → market research → business planner → architect. |
| **Architect as Hub** | Architect is the node after most agents | Architect dispatches to next agents, prepares context, gets summaries, keeps user informed/engaged as needed. Exception: code/qa loop. |
| **Operations Phase** | Big phase not yet developed | Placeholder for future: subagents, documents, metrics, dashboard. |

---

## Open Questions

- [ ] How does the Architect handle pipeline failures? Auto-retry, escalate to user, or abort?
- [ ] What is the minimum viable pipeline for a neo-entrepreneur to see business value?
- [ ] How does the "system in a box" differ from the web service in terms of architecture?
- [ ] What are the specific stages of the Grill Architect's interrogation?
- [ ] How does the user configure autonomy levels (3 or 5)?
- [ ] What external services are available in each connectivity profile?
- [ ] How does the Obsidian integration work? Is it a file sync or MCP?
- [ ] What is the "system in a box" hardware specification? GB10? Other?
- [ ] How does the "variable on product" pricing model work?
- [ ] What legal responsibilities does the user take on by approving documents?

---

## Design Decisions

### Obsidian Vault Location
**Decision:** The Obsidian Vault lives inside the codebase at `storage/vault/`.
**Rationale:** 
- The vault is the source of truth for all documents in the pipeline.
- The pipeline reads from and writes to the vault.
- The user can access the vault through Obsidian on the GB10 box.
- Later replaced by Obsidian MCP integration for real-time sync.

### SonarQube Integration
**Decision:** SonarQube is already running on the GB10 box. Instructions for project usage are available and will be provided to the Architect.
**Rationale:**
- The QA Inspector uses SonarQube to analyze each committed feature.
- The Architect receives the SonarQube report and provides feedback to the Coding Agent.
- The Coding Agent applies changes and re-commits.

### Model Routing
**Decision:** `give-me-model-and-prompt-for(agentphase)` tool queries local SQLite, then SquadShelf, then falls back to defaults.
**Rationale:**
- Agent phases: market research, feature extract, prd, coding, code, deploy, operations.
- Returns model name + system prompt for creating the related agent when the graph is built.
- Default fallbacks:
  - Non-coding: `qwen/qwen3.6-35b-a3b`
  - Coding: `qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled`
- Also available: `google/gemma-4-12b`
- Later replaced by real model library.

### Role-Based Approval
**Decision:** Replaced numeric autonomy levels with **Role-Based Approval**.
### Grill Iteration
**Decision:** Grill stages are done one by one as concepts improve.
**Rationale:**
- Initial grill stages are brainstorming.
- After market analysis, stages are re-iterated to validate/improve each topic.
- Architect asks-proposes and auto-approves with autonomy, motivating choices with facts and sources from market research.
- Always documents with data sources.
- User can approve, edit, or reject at each stage.
- If user grants autonomy, Architect auto-approves but provides more information on strategic and tactical choices in the business plan.

### Grill CEO Mode
**Decision:** If FABIA has CEO role, all decisions are on FABIA but informs user and requests formal sign-off before business launch.
**Rationale:**
- When FABIA acts as CEO, it makes all decisions autonomously.
- FABIA informs the user of decisions and requests formal sign-off before launching the business.
- The user still takes all legal responsibilities by approving key documents and initiatives.

### Subagent Invocation
**Decision:** `invoke_subagent(agent_name, task, prompt, model, subproject_directory, input_files)` tool.
**Rationale:**
- Takes: agent_name, task, prompt (if None takes from give-me-model-and-prompt-for), model (if None takes from function), subproject directory, input files/subvault/subdirectory.
- Best option: Use a LangGraph tool available to the Architect to spin up subagents.
- Allows the Architect to dynamically invoke subagents during the pipeline.

### Model Routing
**Decision:** `give-me-model-and-prompt-for(agentphase)` can be a simple external function or @tool added to the Architect.
**Rationale:**
- Returns model name + system prompt for creating the related agent when the graph is built.
- Can be a simple external function (easier to test, maintain, and debug).
- Or an @tool (more integrated with the Architect's toolset).
- Default fallbacks:
  - Non-coding: `qwen/qwen3.6-35b-a3b`
  - Coding: `qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled`
- Also available: `google/gemma-4-12b`
- Later replaced by real model library.

### Market Research Helper
**Decision:** Market research agent is a re-engagable helper node.
**Rationale:**
- The Architect can re-engage the market research agent anytime needed.
- Can loop back: architect → market research → business planner → architect.
- This allows the Architect to get additional market data to validate/improve ideas during the grill.

### Architect as Hub
**Decision:** Architect is the node after almost all agents.
**Rationale:**
- The Architect dispatches to the next agents, prepares context for the next agent, and gets the summary from each agent.
- The Architect keeps the user informed/engaged as needed.
- Exception: code/qa loop (the Architect is not in the middle of this loop).

### Operations Phase
**Decision:** Placeholder for future development.
**Rationale:**
- Operations is a big phase not yet developed.
- Will include: subagents, documents, metrics, dashboard.
- Added as a placeholder to keep in mind.

### OpenCode Execution
**Decision:** Use option 2 (subprocess) for execute_opencode.
**Rationale:**
- Option 2 (subprocess): Calls opencode CLI directly via subprocess.
  - Pros: Simple, reliable, easy to debug, no coupling to LangGraph internals.
  - Cons: Less integration with LangGraph state, harder to chain with other LangGraph nodes.
- Option 3 (LangGraph node): Integrate opencode as a LangGraph node.
  - Pros: Better integration with LangGraph state, easier to chain with other nodes.
  - Cons: More complex, harder to debug, couples opencode to LangGraph internals.
- Decision: Use option 2 for now (subprocess) because it's simpler and more reliable. Can migrate to option 3 later if needed.

### Project Naming
**Decision:** FABIA creates code name and folder structure with user.
**Rationale:**
- Once FABIA understands the idea and brainstorms with the user, it proposes a code name (not brand yet).
- Creates project folder structure and agent directories.
- Project name change will be explicit later, not automatic.

### Grill Iteration
**Decision:** Grill stages are re-iterated after market analysis.
**Rationale:**
- Initial grill stages are brainstorming.
- After market analysis, stages are re-iterated to validate/improve each topic.
- Architect asks-proposes and auto-approves with autonomy, motivating choices with facts and sources from market research.
- User can approve, edit, or reject at each stage.

---

## Literature-Backed Best Practices

> Sources reviewed: Tomašev et al. (Distributional AGI Safety, Intelligent AI Delegation, Virtual Agent Economies); Merrill et al. (Terminal-Bench 2.0); Dihlmann et al. (Arbor); Wan Team (Wan-Streamer).

### 1. Intelligent Delegation Framework
*Source: Tomašev et al., "Intelligent AI Delegation" (2026).*

Delegation is not just task decomposition — it is a transfer of **authority, responsibility, accountability**, with clear **roles and boundaries** and mechanisms for **trust**.

**Five requirements for intelligent delegation:**

| Requirement | Meaning for FABIA |
|-------------|-------------------|
| **Dynamic Assessment** | Model router tracks capability, reliability, cost, latency, and current load per agent/model; assigns tasks dynamically rather than statically |
| **Adaptive Execution** | Architect can reassign or abort a subagent mid-execution if performance degrades; fallback models are active, not just configured |
| **Structural Transparency** | Every delegation is logged: who delegated what to whom, with what authority, and what the outcome was; DAG checkpoints provide audit trail |
| **Scalable Market Coordination** | `invoke_subagent` becomes a mini market: agent name, task, prompt, model, budget, input files, and expected deliverables |
| **Systemic Resilience** | Strict role-based permissions prevent scope creep; redundant agents and bounded operational scopes limit cascading failures |

**FABIA integration:**
- Extend `invoke_subagent(agent_name, task, prompt, model, subproject_dir, input_files)` with explicit **authority transfer** and **accountability fields**.
- Add **delegatee capability inference** to the model router (not just average score, but current state: context-window load, recent success/failure on similar tasks).
- Store delegation decisions in the audit log.

### 2. Distributional AGI Safety
*Source: Tomašev et al., "Distributional AGI Safety" (2026).*

AGI may first emerge as a **patchwork** of coordinated sub-AGI agents rather than a single monolith. Safety therefore requires safeguards at the **collective** level, not just per-agent alignment.

**Key concepts:**
- **Patchwork AGI** → collective capability exceeds individual capability
- **Sandbox economies** → impermeable or semi-permeable environments for agent transactions
- **Market mechanisms + reputation + auditability + oversight** → collective risk mitigation
- **Standardized protocols** (MCP, A2A) → interoperability

**FABIA integration:**
- Treat FABIA itself as a patchwork system: the Architect orchestrates specialists, none of which is "the business" alone.
- Keep coding/deployment execution inside **Docker sandboxes**; treat external API calls as semi-permeable boundaries requiring approval.
- Add a **reputation ledger** per agent/model in `.fabia_data/model_scoring.db`.
- Plan support for **MCP/A2A protocols** when exposing FABIA agents to external tools.
- Human role is **orchestration and verification**, not micromanagement.

### 3. Virtual Agent Economies
*Source: Tomašev et al., "Virtual Agent Economies" (2025).*

Autonomous agents are forming an economic layer. Design choices matter along two axes: **emergent vs. intentional** origins, and **permeable vs. impermeable** boundaries.

**Mechanisms to adopt:**
- **Auction-based resource allocation** for shared compute/tools when multiple subagents compete
- **Mission economies** to coordinate agents around portfolio-level goals
- **Verifiable Credentials / reputation** to establish trust between agents
- **Guardrails** for hallucination, sycophancy, adversarial manipulation
- **Sector-specific permeability** — high-risk actions (deploy, external spend) in impermeable sandboxes; low-risk research actions more permeable

**FABIA integration:**
- Operations phase becomes a **mission economy**: each portfolio company is a "mission"; agents bid internal credits for tasks.
- High-risk stages (deploy, payments, legal commits) run in **impermeable sandboxes** with mandatory human approval.
- Market Analyst / research stages can be **semi-permeable** (web access allowed, but with logging).

### 4. Terminal-Bench
*Source: Merrill et al., "Terminal-Bench 2.0" (2026).*

Hard, realistic CLI benchmark for agents. Key quality principles:
- **Outcome-driven** evaluation, not process-driven
- **Docker-isolated** task environments
- **Anti-cheat design**: no oracle solutions in containers, no future commits, adversarial exploit checks
- **Manual verification** of tasks before inclusion
- **Harbor** framework for running evals at scale

**FABIA integration:**
- Coding Agent tests should run in **fresh Docker containers** per task.
- QA Inspector should combine **SonarQube (static)** + **outcome-based tests (functional)**.
- Build a **FABIA eval harness** (similar to Harbor) for agent benchmarks: market-research quality, PRD completeness, code correctness, deploy success.
- Add **anti-cheat checks** to evaluation datasets: remove oracle solutions, prevent shortcut exploitation.

### 5. Cross-Cutting Best Practices

| Practice | Source | FABIA Action |
|----------|--------|--------------|
| Role-based authority and bounded scopes | Intelligent Delegation | Approval gates tied to roles; `invoke_subagent` carries authority field |
| Continuous reputation tracking | Distributional AGI Safety + Virtual Agent Economies | Model router scores per task/agent/project |
| Auditability and attribution | Intelligent Delegation | DAG checkpoints + delegation logs |
| Sandboxed execution | Distributional AGI Safety + Virtual Agent Economies | Docker for code/test/deploy; impermeable for high-risk |
| Outcome-driven evaluation | Terminal-Bench | Functional tests, not just static checks |
| Standardized agent protocols | Distributional AGI Safety | Roadmap MCP/A2A support |
| Human orchestration + verification | Distributional AGI Safety | Architect as hub, user as final approver |

---

*This document is updated during grilling sessions. Do not treat it as a spec.*

---

## Grilling Session — Executing Pipeline (2026-07-04)

Scope: how the FABIA v0.3 pipeline executes, fails, retries, and resumes.

### Current Pipeline Flow

```text
START (document_ingestion)
    ↓
grill_architect  — human approval gate
    ↓
market_analyst   — can loop back to grill_architect
    ↓
prd_generator    — human approval gate
    ↓
feature_mapper   — human approval gate
    ↓
coding_agent ↔ testing_agent ↔ qa_inspector  — internal TDD/QA loop
    ↓
deploy_agent     — human approval gate
```

Revision loops exist for PRD (market_analyst_revision) and code/QA (coding_agent_revision). Both have max-revision guards.

### Open Questions for This Session

1. **Failure policy after max revisions.** If a stage still fails after the allowed number of revisions, does the pipeline abort, escalate to the user, or fall back to a simpler path?
2. **Retry/backoff semantics.** Are retries immediate, fixed-delay, or exponential? Does the model router switch models on retry?
3. **Human escalation granularity.** Does the user see a full artifact, a diff, or just a summary when asked to resolve a stuck stage?
4. **Checkpoint resume scope.** Can the user restart from any prior checkpoint, or only from the last approval gate?
5. **Code/QA loop concurrency.** Is the coding_agent → testing_agent → qa_inspector loop sequential or can testing/QA run in parallel across features?
6. **Resource / cost boundaries.** Who decides when a revision is too expensive (token burn, compute time) and what action is taken?

### Decision Log

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
|   |          |           |        |
