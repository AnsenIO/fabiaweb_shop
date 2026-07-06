# AGENTS.md — Static Context for FABIA v0.3

> **Purpose:** This file is the single source of static context for any coding agent (Claude, Gemini, OpenCode, etc.) working on the FABIA codebase. Read it before modifying code. For dynamic per-agent memory, see `.fabia_agents/<agent>/memory_as_tool.md`.

---

## 1. Project Identity

**FABIA** = **F**ully **A**utonomous **B**usiness **I**ntelligence **A**rchitect  
**Version:** v0.3  
**Owner:** IABAI (internal use only)  
**Mission:** Take a raw founder idea—optionally enriched with uploaded documents—and orchestrate the complete product lifecycle through a fleet of specialized sub-agents, from market analysis to deployed product, on sovereign local infrastructure.

### High-Level Architecture

```text
User Idea
    ↓
Market Analyst Agent → PRD Generator Agent → Feature Mapper Agent
    ↓
Coding Agent → Testing Agent → QA Inspector Agent → Demo Deploy Agent

All transitions flow through the FABIA Orchestrator (Flask API + LangGraph),
which enforces approval gates, schema validation, model routing, and checkpoint persistence.
```

The pipeline is a **linear DAG** with **revision loops**:

- PRD failure → `market_analyst_revision`
- Test/QA failure → `coding_agent_revision`
- Both loops have **max-revision guards** to prevent infinite ReAct cycles.

---

## 2. Repository Layout

```
/home/ansen/projects/fabia-0.3/
├── AGENTS.md                    # This file
├── README.md                    # Human-facing project overview
├── docker-compose.yml           # Service topology
├── fabia-architecture.html      # Interactive architecture diagram
├── docs/
│   ├── PRD.md                    # Canonical PRD with SDLC-AI alignment
│   ├── PRD-fabia-v0.3-decision-architecture.md  # Decision architecture
│   ├── FEATURES.md               # Epic/task decomposition
│   └── TASKS.md                  # Task backlog with acceptance criteria
├── src/
│   ├── admin/
│   │   ├── __init__.py
│   │   └── app.py                # Admin dashboard / FABIABox UI
│   ├── demo/
│   │   ├── __init__.py
│   │   └── app.py                # Deployed product demo + demo endpoints
│   └── orchestrator/
│       ├── api.py                # Flask API entry point
│       ├── graph.py              # LangGraph DAG definition
│       ├── model_router.py       # Model + prompt resolution
│       ├── llm_client.py         # Thin LM Studio / OpenRouter client
│       ├── agents/               # One module per sub-agent
│       │   ├── market_analyst.py
│       │   ├── prd_generator.py
│       │   ├── feature_mapper.py
│       │   ├── coding_agent.py
│       │   ├── testing_agent.py
│       │   ├── qa_inspector.py
│       │   ├── deploy_agent.py
│       │   └── grill_architect.py
│       ├── document_ingestion.py # Uploaded document extraction and context injection
│       ├── schema_validator.py   # JSON schema validation
│       ├── approval_gates.py     # Interrupt / resume helpers
│       ├── checkpointing.py      # SQLite checkpoint persistence
│       ├── reputation_ledger.py  # Per-model scoring DB
│       ├── coding_bridge.py      # OpenCode CLI bridge
│       └── delegation.py         # Subagent invocation audit log
├── tests/                       # Unit tests for harness components
├── .fabia_agents/               # Per-agent memory + KV cache
├── .fabia_data/                 # SQLite checkpoints + scoring DB
└── storage/                     # Generated artifacts per pipeline run
    ├── artifacts/<run-id>/
    │   ├── market_research.json
    │   ├── prd_dossier.json
    │   ├── task_mapping.json
    │   └── code_artifacts.json
    └── projects/<slug>/
        ├── vault/
        └── uploads/             # User-uploaded .md/.txt/.pdf files + extracted text
```

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.13+ |
| Package Manager | `uv` |
| Orchestration | LangGraph + Flask API |
| Persistence | SQLite3 (checkpoints, model scoring) |
| LLM Inference | LM Studio on `localhost:1234` |
| Primary Model | `qwen/qwen3.6-35b-a3b` (general tasks), `qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled` (coding/QA) |
| Coding Bridge | `opencode` CLI (planned) |
| Static Analysis | SonarQube (`scripts/run-sonar.sh`) |
| Containerization | Docker Compose |

### Local Inference Path

```text
FABIA Orchestrator
    LMSTUDIO_URL=http://localhost:1234/v1/chat/completions
        ↓
    LM Studio on 127.0.0.1:1234 (OpenAI-compatible /v1/chat/completions)
        ↓
    qwen/qwen3.6-35b-a3b  (general tasks)
    qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled  (coding / QA)
```

To use OpenRouter for a specific model, prefix its id with `openrouter/` and set `OPENROUTER_API_KEY`.

---

## 4. Docker Service Map

Defined in `docker-compose.yml`:

| Service | Container Name | Host Port | Purpose |
|---|---|---|---|
| `orchestrator` | `fabia-orchestrator` | `8021` | Flask API + LangGraph engine |
| `demo` | `fabia-demo` | `8091`→`80`, `9011`→`9000` | Deployed product demo + demo endpoints |
| `admin` | `fabia-admin` | `4021` | Admin dashboard / FABIABox UI |

### Shared Volumes

- `./storage` → artifact persistence
- `./.fabia_data` → SQLite checkpoints + scoring DB
- `./.fabia_agents` → per-agent memory + KV cache

---

## 5. Common Commands

```bash
# Start all services
cd ~/projects/fabia-0.3
docker-compose up -d

# Start only the orchestrator for local dev
docker-compose up -d orchestrator

# Run tests
uv run pytest tests/

# Run SonarQube static analysis
./scripts/run-sonar.sh

# Verify LM Studio is reachable
curl http://localhost:1234/v1/models

# Trigger a pipeline run with optional uploaded documents
curl -X POST http://localhost:8021/api/run \\
  -H "Content-Type: multipart/form-data" \\
  -F 'idea={"text":"A team Pomodoro timer with Slack integration"}' \\
  -F "documents=@/path/to/background.md" \\
  -F "documents=@/path/to/brief.pdf"

# Upload additional documents to an active pipeline
curl -X POST http://localhost:8021/api/upload/<pipeline_id> \\
  -F "documents=@/path/to/extra.txt"
```
---

## 6. Agent Nodes & Responsibilities

| Node | Source File | Responsibility |
|---|---|---|
| `grill_architect` | `src/orchestrator/agents/grill_architect.py` | Pre-flight stress-test; interrupts with clarifying questions |
| `market_analyst` | `src/orchestrator/agents/market_analyst.py` | Deep market research, competitor mapping, TAM sizing |
| `prd_generator` | `src/orchestrator/agents/prd_generator.py` | Convert approved business plan into structured PRD |
| `feature_mapper` | `src/orchestrator/agents/feature_mapper.py` | Decompose PRD into epics, atomic tasks, dependency graph |
| `coding_agent` | `src/orchestrator/agents/coding_agent.py` | Generate code via `opencode` CLI against local LLM |
| `testing_agent` | `src/orchestrator/agents/testing_agent.py` | Run tests in isolated Docker container |
| `qa_inspector` | `src/orchestrator/agents/qa_inspector.py` | Static analysis, SonarQube gates, quality metrics |
| `deploy_agent` | `src/orchestrator/agents/deploy_agent.py` | Deploy approved build to FABIABox LAN |
| `api` | `src/orchestrator/api.py` | Flask API, model routing, schema validation, checkpointing |
| `graph` | `src/orchestrator/graph.py` | LangGraph DAG definition and conditional edges |

### DAG Order

```text
market_analyst → prd_generator → feature_mapper → coding_agent → testing_agent → qa_inspector → deploy_agent
```

A `document_ingestion` node runs at `START` and is re-entrant via `POST /api/upload/<pipeline_id>`. Uploaded documents are injected into the context of the next relevant agent.

Human approval gates sit between major transitions.

---

## 7. State Schema Conventions

The LangGraph state is defined in `src/orchestrator/graph.py` and persisted to SQLite at:

```text
.fabia_data/state/dag_checkpoints.db
```

Key state fields (do not rename without updating `graph.py` and `api.py`):

| Field | Purpose |
|---|---|
| `idea` | Raw user input |
| `uploaded_documents` | List of `UploadedDocumentArtifact` records |
| `market_research` | Output from Market Analyst |
| `business_plan` | Approved plan from Orchestrator gate |
| `prd_dossier` | Output from PRD Generator |
| `task_mapping` | Output from Feature Mapper |
| `code_artifacts` | Output from Coding Agent |
| `test_report` | Output from Testing Agent |
| `qa_report` | Output from QA Inspector |
| `deploy_result` | Output from Deploy Agent |
| `revision_count_*` | Counters guarding max revisions |

### UploadedDocumentArtifact Schema

```json
{
  "filename": "pitch-deck.pdf",
  "mime_type": "application/pdf",
  "original_path": "storage/projects/<slug>/uploads/pitch-deck.pdf",
  "extracted_text_path": "storage/projects/<slug>/uploads/pitch-deck.extracted.txt",
  "word_count": 1240,
  "uploaded_at": "2026-06-30T12:00:00Z"
}
```

---

## 8. Prompt & System-Prompt Conventions

### Current State (v0.3)

- System prompts are loaded from `prompts/<agent>.md` markdown files.
- The loader is `orchestrator.model_router._load_prompt` (used by `ModelRouter`).
- Each prompt file contains YAML frontmatter with `version`, `model`, and `phase` metadata, followed by the system prompt body.
- Uploaded document ingestion is handled by `src/orchestrator/document_ingestion.py`.

### Example Prompt File

```text
---
version: "1.0"
phase: coding
model: qwen3.6-35b-a3b-kimi-k2.6-reasoning-distilled
---
You are the FABIA Coding Agent...
```

### Target Conventions (SDLC-AI Best Practice)

Move runbook-style guidance out of prompts and into versioned skill packages:

```text
prompts/
├── market_analyst.md
├── prd_generator.md
├── feature_mapper.md
├── coding_agent.md
├── testing_agent.md
├── qa_inspector.md
└── deploy_agent.md
skills/
└── <agent>/
    └── SKILL.md
```

Each prompt file should include:

1. **Role statement** — who the agent is.
2. **Task definition** — what it must produce.
3. **Output schema** — exact JSON shape expected.
4. **Constraints** — hard rules (no secrets, no unsafe calls).
5. **Examples** — 1-2 few-shot examples for complex tasks.

When modifying prompts:

- Increment the version field.
- Run `tests/test_model_router.py` and `tests/test_schema_validator.py`.
- Do not commit secrets or credentials inside prompt templates.

---

## 9. Document Ingestion Conventions

FABIA v0.3 treats user-uploaded documents as first-class inputs.

### Supported Formats
| Format | Extension | Extraction Method |
|---|---|---|
| Markdown | `.md` | Read as UTF-8 text |
| Plain text | `.txt` | Read as UTF-8 text |
| PDF | `.pdf` | Local parser (`pymupdf` or `pdfplumber`) |

### Storage Layout
```text
storage/projects/<slug>/
└── uploads/
    ├── pitch-deck.pdf              # original file
    └── pitch-deck.extracted.txt  # extracted plain text
```

### API Endpoints
- `POST /api/run` accepts `multipart/form-data` with `idea` (JSON) and optional `documents` files.
- `POST /api/upload/<pipeline_id>` appends documents to an active pipeline.
- `GET /api/documents/<pipeline_id>` lists uploaded documents.

### Context Injection
Extracted text is appended to the agent prompt under:
```text
[User-Provided Documents]
- pitch-deck.pdf (1240 words)
  <extracted text>
```

Agents must cite which uploaded documents influenced their output.

---

## 10. Guardrails Already in Place

These constraints are implemented and must be preserved:

| Guardrail | Location | Behavior |
|---|---|---|
| **Approval Gates** | `src/orchestrator/approval_gates.py` | Human-in-the-loop via LangGraph `interrupt()` |
| **Schema Validation** | `src/orchestrator/schema_validator.py` | Validates agent output against expected JSON schema |
| **Max Revision Guards** | `src/orchestrator/graph.py` | Limits ReAct revision loops |
| **Model Routing** | `src/orchestrator/model_router.py` | Routes tasks by task type + score |
| **Memory-as-a-Tool** | `src/orchestrator/graph.py` | Loads per-agent `memory_as_tool.md` |
| **SQLite Checkpointing** | `src/orchestrator/checkpointing.py`, `graph.py` | DAG state snapshots for rollback/resume |
| **Document Type Validation** | `src/orchestrator/document_ingestion.py` | Rejects unsupported file types before extraction |

### Guardrails to Add (SDLC-AI Roadmap)

- Deterministic pre/post hooks for generated code (block `eval`, `exec`, `os.system`, hardcoded secrets).
- File-path sandboxing — generated code may only write under `storage/` and project temp dirs.
- Import validation — generated code may only use allowed dependency list.
- Token/cost metering per node.

---

## 11. Where to Add New Harness Code

| Capability | Suggested Location |
|---|---|
| Eval harness / rubrics | `evals/` directory + `src/orchestrator/evaluator.py` |
| Deterministic guardrails | `src/orchestrator/guardrails.py` |
| MCP servers for tools | `src/mcp/` or `mcp_servers/` |
| A2A cross-agent protocol | `src/a2a/` |
| Structured observability / traces | `.fabia_data/traces/` + `src/orchestrator/telemetry.py` |
| Economic model routing profiles | Extend `ModelRouter` in `src/orchestrator/model_router.py` |
| Agent Skills loader | `skills/<agent>/SKILL.md` + `src/orchestrator/skills.py` |
| Document ingestion | `src/orchestrator/document_ingestion.py` |

---

## 12. Testing Conventions

- Use `pytest`.
- Tests for harness components live in `tests/`.
- When adding a new node or utility, add a corresponding `tests/test_<name>.py`.
- Run the full suite before opening a checkpoint for human approval.

Existing tests to keep green:

- `tests/test_approval_gates.py`
- `tests/test_dag_checkpointing.py`
- `tests/test_document_ingestion.py`
- `tests/test_model_router.py`
- `tests/test_nodes_parse_json.py`
- `tests/test_memory_as_tool.py`
- `tests/test_schema_validator.py`
- `tests/test_web_api.py`

---

## 13. Secrets & Security Policy

**Never commit secrets, API keys, tokens, or credentials to this repository.**

- Store inference endpoints, OAuth tokens, and deployment keys in environment variables or Docker secrets.
- If a generated artifact contains a secret, replace it with `[REDACTED]` immediately.
- The `coding_agent` must externalize all credentials to env vars and fail generation if secrets are embedded.
- Review `prd_dossier.json`, `task_mapping.json`, and `code_artifacts.json` in `storage/artifacts/` for accidental secret leakage before deploying.
- Uploaded documents may contain sensitive business information; store them only under `storage/projects/<slug>/uploads/` and do not log full contents.

---

## 14. Contribution Rules for Agents

Before making any non-trivial change:

1. Read this file.
2. Read the relevant section of `docs/PRD.md`, `docs/FEATURES.md`, or `docs/TASKS.md`.
3. Read the target source file and its tests.
4. Preserve the existing DAG order and state schema.
5. Add or update tests for harness changes.
6. Run `uv run pytest`.
7. Summarize changes with file references in your response.

When in doubt, prefer small, verifiable changes over large refactors.
