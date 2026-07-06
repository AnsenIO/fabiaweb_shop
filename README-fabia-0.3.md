# FABIA Orchestrator v0.3

|**Sovereign AI Business Architect** — Fleet of specialized sub-agents orchestrating autonomous multi-company portfolio management from raw idea to deployed product, running on local sovereign infrastructure (LM Studio). SquadShelf integration evolves into a functional model and prompt library. v0.3 adds native support for user-uploaded documents (`.md`, `.txt`, `.pdf`) as first-class inputs at any pipeline stage.

## Purpose
FABIA takes a raw user-provided business **Idea**—optionally enriched with uploaded documents—and orchestrates the complete lifecycle through a fleet of autonomous sub-agents, from initial market analysis to deployed product on FABIABox (GB10 LAN). Port 80 is reserved for the Demo Deploy Agent's output (serving the user's deployed application); basic FABIABox admin/dashboard remains, while advanced process mining UI progresses in later releases. Manages formal human approval gates and dynamically consults model/prompt libraries to route each sub-agent with the best possible inference configuration — starting locally, expandable via user feedback scoring loops.

## Architecture
FABIA operates as an **Agentic Business Process Management System (A-BPMS)** that manages a linear DAG of sub-agents with approval-gate checkpoints for human-in-the-loop governance.

### Core Architectural Pillars
### 1. User-Uploaded Document Ingestion (v0.3)
   FABIA accepts `.md`, `.txt`, and `.pdf` files as first-class inputs:
   - **Upload points:** initial idea submission, at any approval gate, or on demand via the API/dashboard.
   - **Extraction:** Markdown and text are read directly; PDFs are converted to text via a local parser (`pymupdf` / `pdfplumber`).
   - **Context injection:** Extracted content is appended to the relevant agent prompt under a `[User-Provided Documents]` section.
   - **Storage:** Original files and extracted text are saved to `storage/projects/<slug>/uploads/` for audit and reuse.

### 2. Dynamic Model Routing Layer  
   FABIA operates as a centralized routing layer that dynamically assigns the optimal inference configuration to each sub-agent based on task complexity and current scoring data:
   - **Routing Logic:** A lightweight classifier determines the "intent" of the query and routes it to the appropriate worker model.
   - **Creative/Strategic Tasks:** (Market Research, PRD Generation) → `qwen/qwen3.6-35b-a3b` (high reasoning).
   - **Coding/Technical Tasks:** (Coding Agent, QA reasoning) → `qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled` (specialized for syntax and logic).
   - **Scoring Evolution:** For every step, FABIA reports candidate models with current scores + metadata. Users can validate via automated evaluation gates or annotate (+1/-1 score delta). When validation passes, the routing layer updates the scoring DB automatically.

### 3. **Iterative Refinement Loops (ReAct)**  
   While the business logic (Research → PRD) follows a linear DAG, the development phase utilizes ReAct (Reasoning and Acting) loops. QA Inspector rejections trigger back-channels to the Coding Agent with specific error logs, governed by configurable "Max Retry" thresholds before escalating to manual review.

### 4. **Standardized Inter-Agent Protocol**  
   To ensure reliable handoffs between sub-agents (e.g., Feature Mapper → Coding Agent), FABIA uses a strict **JSON Schema** definition for all critical data transfers:
   - **Feature Mapper Output:** Structured JSON defining task dependencies, priority, and required libraries.
   - **Coding Agent Input:** Strictly typed JSON payload ensuring no context is lost during the transfer.
   - **Validation Layer:** The Orchestrator validates the JSON schema before passing it to the next node.

### 5. **Sandboxed Execution Environment**  
   The `Tester Agent` and `QA Inspector` do not run code directly on the host machine:
   - **Isolation:** Every code generation task is spun up in a temporary **Docker Container** (or isolated WSL environment).
   - **Persistence:** Artifacts are saved to a versioned mount point before the container is destroyed to prevent environment drift.

### 6. **Chain-of-Thought Prompting**  
   The Feature Mapper and decomposition nodes utilize explicit Chain-of-Thought reasoning to identify Epics, break them into Atomic Tasks, and determine Dependencies before outputting their final JSON schema. This ensures high-quality decomposition and traceability across the sub-agent fleet.

### DAG Workflow Graph
```mermaid
flowchart TD
    A[User Idea] --> M[Market Analyst Agent]
    F[FABIA Orchestrator + Approval Gate] <-->|brainstorm loops| A
    
    M --> MP[Model/Prompt Library Consultant]
    
    subgraph Sub-Agent Fleet
        direction TB
        PRD[PRD Generator Agent] -.-> FM[Feature Mapper Agent]
        FM -.-> COD[Coding Agent]
        COD -.-> TES[Tester Agent]
        TES -.-->|issues found| COD
        QAI[QA Inspector Agent]
    end
    
    F --> PRD
    QAI -->|approve| DEP[Demo Deploy Agent]
    QAI -->|fail + report| COD

    MP -->|model scoring\nguides| PM[Memory-as-a-Tool File\n`memory_as_tool.md`]
    MP ---|dynamic routing & prompt selection| PRD
    MP ---|dynamic routing & prompt selection| FM
    MP ---|dynamic routing & prompt selection| COD
    MP ---|dynamic routing & prompt selection| TES
    MP ---|dynamic routing & prompt selection| QAI
    PM <--> FM
```

## Core Sub-Agents & Lifecycle
Each sub-agent operates autonomously regarding *how* it achieves its step, but bounded by FABIA's DAG, approval gates, model routing, and memory system. Every agent has its own **INPUT/OUTPUT**, persistent memory space (`$HOME/projects/$PROJECTNAME/.fabia_agents/<name>/`), and KV cache for attention persistence (arXiv:2603.04428).

### 1. Market Analyst
- **Inputs:** Raw user idea (text) + optional uploaded documents (`.md`, `.txt`, `.pdf`)
- **Process:** Deep market research, competitor mapping, segmentation analysis, demand validation across sources (arXiv papers, business databases). Uploaded documents are treated as additional background material and quoted where relevant.
- **Outputs:** Structured `market_research_dossier.md` in `$PROJECT/research/market_findings_v{N}/` folder
- **Memory/Space:** Own JSONL transcript of all crawl/query tool calls + memory-as-tool notes from past research feedback

### 2. FABIA Orchestrator (Approval Gate)
- **Inputs:** Market dossier → user brainstorm interaction
- **Process:** Brainstorms validated business plan with user; enforces formal human approval gates before any sub-agent executes
- **Outputs:** Approved `business_plan.md` + frozen DAG checkpoint in SQLite3 DB
- **Memory/Space:** Own memory space with full history of all user interactions, approvals, and model scoring per-step scores

### 3. PRD Generator Agent
- **Inputs:** Approved business plan + market dossier
- **Process:** Converts to structured PRD (functional requirements, non-functional requirements, user stories) using peer-reviewed arXiv-backed best practices for Agentic AI product design
- **Outputs:** `prd_dossier.md` for user validation & formal approval sign-off
- **Memory/Space:** Own memory space storing prior prompts/models used + scoring feedback from previous revisions

### 4. Feature Mapper Agent (Decomposition Engine)
- **Inputs:** Approved PRD dossier (JSON/Markdown)
- **Process:** Implements a **Top-Down Decomposition** engine:
  1. **Epics (Grouping):** Groups related PRD requirements into logical "Epics" (e.g., "User Auth," "Payment Gateway").
  2. **Atomic Tasks (Breaking Down):** Breaks Epics into single, executable coding tasks (e.g., "Create Database Model for Users").
  3. **Dependency Graph (Ordering):** Determines execution order (e.g., "DB Model" before "Stripe Hook").
- **Outputs:** Strict `task_mapping.json` (see Schema below) + DAG execution graph.
- **Memory/Space:** Tracks past decomposition decisions, prioritization lessons, and recurring tech stack patterns.

### 5. Coding Agent (OpenCode Bridge)
- **Inputs:** Prioritized feature tasks + git branch-per-feature convention
- **Process:** Manages `opencode` CLI calls against local LM Studio endpoints; enforces test-first development mandates; cycles issues back to Testing Agent until green
- **Outputs:** Feature branches with tests + passing CI per-feature
- **Memory/Space:** Own memory space storing coding conventions learned, prompt versions used for code generation, feedback from past iterations

### 6. Tester Agents (Verification Engine)
- **Inputs:** Code feature branches + PRD requirements as acceptance criteria
- **Process:** Executes automated test suites inside an **isolated Docker Container**; validates environment constraints match PRD specifications; returns structured failure reports (stdout/stderr) to Coding Agent.
- **Outputs:** Test report per-issue with PASS/FAIL + diff of expected vs actual
- **Memory/Space:** Own memory space storing test patterns learned, false positive history, agent-specific validation heuristics

### 7. QA Inspector Agent
- **Inputs:** Clean build (all features passing tests)
- **Process:** Performs static analysis and SonarQube-style quality gates; validates architecture consistency, code metrics, and security posture
- **Outputs:** Quality gate report with pass/fail for each criterion + architectural linting results
- **Memory/Space:** Own memory space storing quality thresholds learned across projects, past QA violation patterns

### 8. Demo Deploy Agent (Infrastructure Manager)
- **Inputs:** Clean build approved by QA Inspector
- **Process:** Provisions GB10 LAN environment, handles dependency graphs, FABIABox service discovery + web interface deployment (port 80 for web admin, ports 4021/9011 for demo endpoints)
- **Outputs:** Live URL on FABIABox LAN for user testing + infrastructure health check report. Port 80 is reserved for serving the deployed product demo; basic FABIABox admin/dashboard remains, while advanced process mining UI progresses to v0.4+.
- **Memory/Space:** Own memory space storing deployment configs learned per-project, past environment issue resolutions

## Model & Prompt Library Consultant
FABIA acts as a centralized consultant for models and system prompts, allowing each sub-agent to be deployed with the optimal inference configuration.

### System Prompt JSON Structure (v0.3)
Each agent's system prompt is stored in a dedicated file named `agent-name-systemprompt.json` within `$PROJECT/.fabia_prompts/`. The JSON structure includes versioning and metadata fields:

```json
{
  "version": "1.0",
  "created_date": "2024-01-15T10:30:00Z",
  "last_updated": "2024-02-20T14:45:00Z",
  "agent_name": "market_analyst",
  "description": "System prompt for the Market Analyst agent. Responsible for deep market research and competitor mapping.",
  "prompt_template": 
    "You are FABIA's Market Analyst Agent. You specialize in comprehensive market research...",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "model_variant": "qwen/qwen3.6-35b-a3b"
  },
  "tags": ["research", "competitor-analysis", "market-segmentation"]
}
```

The placeholder function `get_system_prompt(agent_name)` in v0.3 loads this JSON, extracts the `prompt_template`, and injects it into the agent's context. **These placeholder functions are intentionally minimal and functional — they will be replaced with fully SquadShelf-integrated methods in v0.4.**

### System Prompt Scoring Mechanism
For every step in the pipeline, FABIA reports a **scored list of candidate system prompts**, ranked by historical performance. Users can annotate/feedback on any prompt:
- **+1 score delta:** Approve — raises that prompt's score; makes it more likely to be selected next time
- **-1 score delta:** Reject — lowers its score permanently until re-evaluated
- `0` = Neutral/no preference

FABIA converts these transient critiques into retrievable guidelines via the **Memory-as-a-Tool pattern** (arXiv:2512.09543): feedback is written to `$PROJECT/.fabia_memory/agent_name/memory_as_tool.md` for the next invocation's context injection. No re-reasoning needed — agent loads scored prompts + user feedback as in-context memory.

## State Persistence Architecture (v0.3)
FABIA uses a **hybrid state management pattern** combining industry best practices and peer-reviewed research findings:

| Storage Layer | Technology | Purpose |
|--------------|------------|---------|
| **DAG Checkpoints** | SQLite3 (`checkpoints` table) | Complete node state snapshots at each pipeline step. CRUD checkpointing — rollback via `restore(checkpoint_id)` on rejection (LangGraph pattern). Approval gate creates frozen checkpoints. |
| **Agent Transcripts** | Per-agent JSONL files | Each agent's conversation logs, tool invocations, and results in `$HOME/projects/$PROJECTNAME/.fabia_agents/<name>/transcript.jsonl`. Auto-saved continuously like Claude Code. |
| **Memory-as-a-Tool** | YAML/Markdown files | Distilled feedback from user reviews → structured `memory_as_tool.md` per agent. Injected into next invocation context per arXiv:2512.09543 pattern. |
| **Uploaded Documents** | Original files + extracted text (`storage/projects/<slug>/uploads/`) | User-provided `.md`, `.txt`, `.pdf` files and their extracted text, persisted for audit and context injection. |
| **KV Cache Persistence** | Minimalist JSON placeholder (`$PROJECT/.fabia_memory/<agent_name>/kv_cache.json`) | Per-agent lightweight attention state vectors (v0.3). Foundation for full Q4 quantized `.safetensors` persistence (arXiv:2603.04428) in v0.4+. Prevents environment drift by storing structured state that will evolve into persistent KV cache management. |
| **Scoring Database** | SQLite3 (`model_scoring` table) | Tracks system prompt + model scores per step, user feedback deltas, and learned lessons for FABIABox admin analytics dashboard. |

### FABIA Checkpointing Rules
1. Every completed pipeline step auto-checkpoints to `checkpoints` table with status `pending_approval`
2. User approval via FABIABox web UI → checkpoint marked `approved`, child steps unblocked
3. User rejection → checkpoint marked `rejected_with_feedback`, rollback to nearest parent node for rework
4. All tool calls logged at every step → feed to process mining (arXiv:2601.18833 A-BPMS paper) for continuous system optimization

### Agent-to-Agent Handoff Protocol
Standardized JSON payload between agents prevents context drift and enables model-swapping:

```json
{
  "from_agent": "Market Analyst",
  "to_agent": "PRD Generator", 
  "payload_type": "market_research_dossier",
  "artifact_path": "$PROJECT/research/market_findings_v1.md",
  "metadata_scores": {
    "prompt_version": "v2.3",
    "model_used": "qwen/qwen3.6-35b-a3b",
    "scoring_delta": "+1" 
  }
}
```

### Feature Mapper Output Schema (Strict JSON)
The Feature Mapper outputs a rigid JSON structure to serve as the "contract" for the DAG engine and Coding Agent:

```json
{
  "project_context": "E-commerce MVP",
  "estimated_effort_hours": 12,
  "tasks": [
    {
      "id": "T-001",
      "title": "Initialize Database Schema",
      "description": "Create the SQLAlchemy models for Users, Products, and Orders based on the ERD.",
      "priority": "P0",
      "depends_on": [],
      "acceptance_criteria": [
        "Database migration runs successfully",
        "All tables are created in SQLite"
      ],
      "tech_stack": ["SQLAlchemy", "Alembic"]
    },
    {
      "id": "T-002",
      "title": "Implement User Authentication API",
      "description": "Create endpoints for login and registration using JWT.",
      "priority": "P0",
      "depends_on": ["T-001"],
      "acceptance_criteria": [
        "Login endpoint returns 200 with JWT token",
        "Invalid credentials return 401"
      ],
      "tech_stack": ["FastAPI", "PyJWT"]
    }
  ]
}
```

## Development Workflow & Principles
- **Test-first + Commit-per-feature:** No code without tests. Every feature gets its own branch and atomic commit message (verified green before merging to main).
- **Formal Approval Gates:** Every document change requires human sign-off from user, logged with approval record in DB (signature = approval_id + timestamp).
- **Agent Autonomy within Guardrails:** Each sub-agent is autonomous regarding *how* it achieves its step (researching, coding logic, testing methods), bounded by FABIA's DAG routing, model scoring system, and approval gates.
- **Research Document Persistence:** Market analyst data strictly documents sources in dedicated `research/sources/` folder structure to maintain absolute source-of-truth for business plans.
- **Process Mining + Continuous Optimization:** All tool calls → analytics dashboard on FABIABox → auto-optimize prompt parameters as more user feedback accumulates over time (per A-BPMS research principles).


## Tech Stack
| Technology | Purpose |
|-----------|---------|
| Runtime | Python 3.13+ |
| Package manager | `uv` |
| Version control | Git (branch-per-feature, approval-annotated commits) |
| LLM inference | LM Studio `qwen/qwen3.6-35b-a3b` on FABIABox GB10 LAN |
|  | Model routing/local prompt library scoring + evaluation gates | **Business purpose:** SquadShelf-based model library. v0.3 provides functional placeholder tool (`get_system_prompt(agent_name)`) loading `agent-name-systemprompt.json` files with versioning; these placeholders will be replaced by fully functional SquadShelves integration in v0.4+. |
| OpenCode bridge/opencode CLI/subprocess tool calls | Local coding agent orchestration via opencode CLI to Qwen inference endpoint |
| State persistence | SQLite3 (checkpoints, model scoring) + per-agent JSONL transcripts + YAML memory-as-a-tool files + KV cache JSON placeholders in `.fabia_memory/` |
| Architecture docs | `arch.md` (live-updated with every phase/sub-agent change) |

## Current State
- [x] v0.3 kickoff & architecture definition
- [x] User-uploaded document ingestion specification
- [ ] Sub-Agent fleet implementation (8 agents scaffolded)
- [ ] Model/Prompt library consulting layer + scoring DB (SQLite3)
- [ ] Approval gate DAG checkpointing logic
- [ ] FABIABox local demo deployer on GB10 LAN:4021/9011
- [x] System Prompt JSON structure with versioning and placeholder retrieval function (`get_system_prompt(agent_name)`)
- [ ] Process mining dashboard for continuous optimization (v0.4+)
- [ ] Full integration testing across pipeline stages

## SDLC-AI Best Practices Integration

FABIA v0.3 already implements several agentic-engineering patterns from the SDLC-AI playbook (approval gates, schema validation, model routing, memory-as-a-tool, SQLite checkpoints). The following recommendations are tracked for v0.3+ to close the gap between "vibe-coded pipeline" and production-grade agentic engineering:

| Best Practice | Current State | Target Implementation |
|---|---|---|
| **Context Engineering** | `AGENTS.md` exists; prompts loaded from `prompts/<agent>.md` by `src/orchestrator/model_router.py` | Add `CLAUDE.md`; move runbook guidance to `skills/<agent>/SKILL.md` |
| **Agent Skills** | Static `memory_as_tool.md` only | Introduce task-matched skill packages with progressive disclosure |
| **Evals & Rubrics** | Unit tests for harness; no eval dataset or rubrics | Add `evals/` with labeled examples + scoring rubrics per agent node |
| **Trajectory Evaluation** | Output-only schema validation | Evaluate the agent's reasoning path, tool selection, and revision history |
| **Test-First Contracts** | `testing_agent` runs after `coding_agent` (`graph.py:499-500`) | `feature_mapper` emits acceptance criteria; `coding_agent` must satisfy them before testing |
| **Deterministic Guardrails** | Approval gates only | Add pre/post hooks: block secrets, validate imports, sandbox file paths, forbid `eval`/`os.system` |
| **Economic Model Routing** | Fallback defaults in `src/orchestrator/model_router.py` | Route low-complexity tasks to smaller/cheaper models; keep frontier models for architecture/requirements |
| **Observability** | Ad-hoc logging | Structured traces per node: latency, tokens, model, score, drift metrics; surface in Admin dashboard |
| **MCP / A2A Standards** | Direct LLM calls | Wrap file system, git, test runner, deployer as MCP servers; use A2A for cross-agent delegation |
| **Prototype vs Production Modes** | Single `auto_approve` flag (`graph.py:339`) | Harness profiles: `prototype` (light gates, cheap models) vs `production` (full gates, evals, traces) |

Implementation of these items is prioritized by leverage: context files and prompt externalization first, followed by eval rubrics and guardrails. See `docs/PRD.md`, `docs/FEATURES.md`, and `docs/TASKS.md` for the product-level translation of these practices.

## License
Internal use -- IABAI property.

## How to Spin Up FABIABox

### 1. Start LM Studio
Ensure LM Studio is running on the GB10 LAN workstation with its API server enabled on port `1234`.

Verify it's reachable:
```bash
curl http://localhost:1234/v1/models
```

### 2. Start FABIABox Services
Navigate to the project directory and start the orchestrator:
```bash
cd ~/projects/fabia-0.3
docker-compose up -d
```

### 4. Verify Deployment
Check that the services are running on the LAN:
- **Demo Deploy Agent:** `http://<fabia-box-ip>:80`
- **Demo Endpoints:** `http://<fabia-box-ip>:4021` and `:9011`
- **FABIA Orchestrator:** `http://<fabia-box-ip>:8021` (default)

### 5. Access the Admin Dashboard
Basic FABIABox admin/dashboard is available at:
```
http://<fabia-box-ip>:80/admin
```
*(Advanced process mining UI progresses to v0.4+)*
