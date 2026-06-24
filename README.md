# SEJA v2.1.4

> **S**emiotic **E**ngineering **J**ourneys with **A**gents  
> Governance harness for structured agentic development over OpenCode + Docker

[![CI](https://github.com/PUC-Behring-Institute-for-AI/seja/actions/workflows/publish.yml/badge.svg)](https://github.com/PUC-Behring-Institute-for-AI/seja/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/PUC-Behring-Institute-for-AI/seja/branch/main/graph/badge.svg)](https://codecov.io/gh/PUC-Behring-Institute-for-AI/seja)
[![GHCR Downloads](https://img.shields.io/badge/ghcr-puc--behring--institute--for--ai%2Fseja-blue?logo=github)](https://github.com/orgs/PUC-Behring-Institute-for-AI/packages/container/seja)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Agent System](#agent-system)
- [Lifecycle FSM](#lifecycle-fsm)
- [MCP Server](#mcp-server)
- [Security](#security)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [S3 Backup Configuration](#s3-backup-configuration)
- [Reference](#reference)
- [License](#license)

---

## Overview

SEJA is a **governance harness** that structures software development workflows by combining **agentic coding agents** (OpenCode) with a **semiotic engineering** framework. It provides a containerized runtime where AI agents collaborate under explicit lifecycle phases, design intent tracking, and architectural invariants — turning unstructured agent sessions into governed, auditable development processes.

### Why SEJA?

Agentic coding tools (OpenCode, Claude Code, Aider) are powerful but ungoverned: agents can skip design, bypass review, or make decisions without documentation. SEJA wraps the agent runtime with:

- An **FSM lifecycle** (8 states, 19 transitions) that prevents phase skipping
- A **decision registry** with supersession tracking (D-NNN IDs)
- **D16 checker** for multi-step plans (each step validates its predecessor)
- **Semiotic inspection** to measure gaps between intended design and coded reality
- **Dual-write persistence** (SQLite canonical + Markdown for human reading)
- **Litestream backup** with S3 replication for disaster recovery

### How It Works

```mermaid
flowchart LR
    subgraph Host
        A[seja CLI] -->|docker compose| B[Docker Runtime]
    end

    subgraph Containers
        C[seja<br/>MCP + OpenCode] -->|health| D[socket-proxy<br/>Docker API ACL]
        E[litestream<br/>SQLite replication]
        C -->|WAL| E
    end

    subgraph Storage
        F[(SQLite<br/>seja.db)]
        G[.seja/<br/>Markdown Tree]
    end

    C -->|dual-write| F
    C -->|export| G
    
    B --> C
    D -->|GET only| H["/var/run/docker.sock"]
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Semiotic Engineering** | Theory by Clarisse de Souza (2005) — every system is a metacommunication artifact. SEJA extends this to agent governance |
| **FSM Lifecycle** | 8 sequential states: setup → design → research → plan → implement → check → document → reflect |
| **D16 Plans** | Plans with checker steps — step N verifies step N-1 before allowing progress. Named after architectural invariant D16 |
| **Tier Model** | Agents assigned to REASON (slow/deep), CODE (balanced), or FAST (lightweight) tiers |
| **Semiotic Inspection** | Compares designer intent (as-intended) against system behavior (as-coded) using the Semiotic Inspection Method |

---

## Quick Start

```bash
# 1. Install the CLI (sudo required for /usr/local/bin)
sudo curl -fsSL -o /usr/local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/seja"
sudo chmod +x /usr/local/bin/seja

# 2. Setup (~/.seja/ structure + image pull)
seja setup

# 3. Initialize a project
cd ~/projects/my-app
seja init

# 4. Start the container
seja start

# 5. Verify health
seja status
```

---

## Architecture

### Container Design (3 Services)

```mermaid
graph TB
    subgraph "Docker Compose — seja"
        S1[seja<br/>:8765 MCP<br/>:4096 OpenCode]
        S2[socket-proxy<br/>:2375]
        S3[litestream<br/>:—]
    end

    subgraph "Volumes"
        V1[seja-state<br/>/root/.seja-state]
        V2[socket-proxy<br/>/tmp/docker.sock]
        V3[litestream-data<br/>/data/replica]
    end

    S1 -->|seja.db + WAL| V1
    S1 -->|Docker API via proxy| S2
    S2 -->|"/var/run/docker.sock:ro"| D["/var/run/docker.sock"]
    S3 -->|replicate| V1
    S3 -->|snapshots| V3
    
    style S1 fill:#4a90d9,color:#fff
    style S2 fill:#7c3aed,color:#fff
    style S3 fill:#059669,color:#fff
```

| Service | Image | Role | Ports |
|---------|-------|------|-------|
| **seja** | Custom build | MCP server + OpenCode runtime | 8765 (MCP), 4096 (OpenCode) |
| **socket-proxy** | `tecnativa/docker-socket-proxy` | ACL proxy for Docker socket | 2375 (internal) |
| **litestream** | `litestream/litestream` | SQLite WAL replication | — |

### Data Flow

```mermaid
sequenceDiagram
    participant A as Agent<br/>(OpenCode)
    participant M as MCP Server<br/>(FastMCP)
    participant S as SQLite<br/>(seja.db)
    participant MD as Markdown<br/>(.seja/)

    A->>M: seja.decisions.create()
    M->>S: INSERT decisions (canonical)
    S-->>M: OK
    M->>MD: export decisions/D-001.md
    MD-->>M: OK
    M->>A: { id: "D-001", status: "accepted" }

    Note over M,S: Dual-write: SQLite canonical,<br/>Markdown for human reading

    A->>M: seja.constitution.get()
    M->>S: SELECT ... (read-only)
    S-->>M: constitution data
    M->>A: principles, compliance
```

### Module Map

15 MCP modules across 5 categories:

| Category | Modules | Tools | Purpose |
|----------|---------|-------|---------|
| **Core** | project, constitution | 8 | Workspace init, principles, compliance |
| **State** | decisions, design, telemetry | 17 | Decision registry, feature tracking, metrics |
| **Lifecycle** | lifecycle, pending, briefs | 12 | FSM transitions, blockers, session logging |
| **Workflow** | plans, research, perspectives | 12 | D16 plans, recommendations, archetypal views |
| **Analysis** | journeys, tests, experiments | 13 | Semiotic inspection, test runs, parallel forks |

Total: **15 modules**, **64 tools**, **18 SQLite tables**.

### FSM Lifecycle

```mermaid
stateDiagram-v2
    [*] --> setup
    setup --> design: constitution_not_empty
    design --> research: design_intent_defined
    research --> plan: research_recommendation_clear
    plan --> implement: plan_approved
    implement --> check: all_steps_done
    check --> document: all_checks_passed
    document --> reflect: documentation_generated
    reflect --> design: (cycle)

    implement --> design: reason_provided
    implement --> research: reason_provided
    plan --> design: reason_provided
    check --> implement: reason_provided
    reflect --> design: force
```

See [Lifecycle FSM](#lifecycle-fsm) for complete transition table including all 19 transitions and guard conditions.

### Security Layers

```mermaid
graph LR
    L1[Layer 1<br/>Agent frontmatter<br/>allow-lists] --> L2
    L2[Layer 2<br/>MCP invariant<br/>enforcement] --> L3
    L3[Layer 3<br/>Docker socket<br/>proxy ACL] --> L4
    L4[Layer 4<br/>Container<br/>hardening] --> L5
    L5[Layer 5<br/>Cosign<br/>signing]
```

---

## Installation

### Prerequisites

| Requirement | Version | Check | Notes |
|-------------|---------|-------|-------|
| Docker | 24+ | `docker --version` | Install: [docs.docker.com/get-docker](https://docs.docker.com/get-docker) |
| Docker Compose | v2.24+ | `docker compose version` | Included with Docker Desktop; on Linux install separately |
| Git | 2.40+ | `git --version` | |
| Bash | 4+ | `bash --version` | macOS: pre-installed; Linux: `apt install bash` |
| curl | 7+ | `curl --version` | |
| API Key (Anthropic) | — | `export ANTHROPIC_API_KEY=sk-...` | Required for OpenCode agent runtime. [console.anthropic.com](https://console.anthropic.com) |

**Platform notes:**
- **Linux**: Native Docker engine. Ensure your user is in the `docker` group: `sudo usermod -aG docker $USER && newgrp docker`
- **macOS**: Docker Desktop required. The host `/var/run/docker.sock` is mounted read-only via socket-proxy.
- **Windows**: Use WSL2 with Docker Desktop WSL2 backend. Run SEJA inside a WSL2 distribution.

### Option A: One-liner (recommended)

```bash
sudo curl -fsSL -o /usr/local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/seja" \
  && sudo chmod +x /usr/local/bin/seja
seja setup
```

### Option B: Manual download

```bash
# Download from GitHub Releases (sudo required for /usr/local/bin)
VERSION="v2.1.4"
sudo curl -fsSL -o /usr/local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/download/${VERSION}/seja"
sudo chmod +x /usr/local/bin/seja

# Download cosign public key (to home dir, no sudo)
mkdir -p ~/.seja
curl -fsSL -o ~/.seja/cosign.pub \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/download/${VERSION}/cosign.pub"

# Initialize
seja setup --image "ghcr.io/puc-behring-institute-for-ai/seja:${VERSION}"
```

### Option C: From source

```bash
git clone https://github.com/PUC-Behring-Institute-for-AI/seja.git
cd seja

# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -e mcp/[dev]

# Build Docker image
make build

# The CLI is at scripts/seja — use it directly
alias seja=$(pwd)/scripts/seja
seja setup --image ghcr.io/puc-behring-institute-for-ai/seja:latest
```

### Verification

After installation, run the diagnostics suite:

```bash
seja doctor
```

Expected output example:

```
✓ Docker daemon running (24.0.7)
✓ Docker Compose v2.24+ found
✓ Port 8765 available (MCP)
✓ Port 4096 available (OpenCode)
✓ Git 2.40+ configured
✓ Disk space OK (15GB free)
✓ Cosign public key found at ~/.seja/cosign.pub
```

`seja doctor` checks: Docker daemon, compose version, MCP/OpenCode port availability, git config, disk space, cosign public key.

If any check fails, see [Troubleshooting](#troubleshooting) for solutions.

### Directory Structure

After `seja setup`, your `~/.seja/` contains:

```
~/.seja/
├── .env                      # Runtime configuration
├── docker-compose.yml        # Generated compose file
├── docker-compose.override.yml  # Workspace mounts
├── cosign.pub                # Public key for signature verification
├── workspaces.conf            # Registered workspace paths
├── backups/
│   └── litestream/            # Local litestream replicas
├── logs/                      # Container logs
└── tmp/                       # Temporary update files
```

---

## Usage

### CLI Reference — 25+ Subcommands

#### Core

| Command | Description |
|---------|-------------|
| `seja setup [--dry-run] [--no-pull] [--image IMG]` | Initialize `~/.seja/` directory structure and pull image |
| `seja init [path]` | Initialize `.seja/` workspace at path with templates |
| `seja status [--json]` | Show container status, MCP health, workspace info |
| `seja` | (default) Open SEJA OpenCode TUI (start + attach) |
| `seja start` | Start SEJA services (`docker compose up -d`) |
| `seja stop` | Stop SEJA services (`docker compose down`) |
| `seja restart` | Restart SEJA services |
| `seja web` | Open SEJA + OpenCode in the browser |
| `seja logs [service] [--tail N] [--follow]` | View container logs |
| `seja shell [service]` | Open interactive shell in a container |
| `seja exec <cmd>` | Execute command in the SEJA container |
| `seja update [--check]` | Update SEJA to latest version (cosign-verified) |
| `seja version` | Show SEJA version |
| `seja help [cmd]` | Show help for a specific command |

#### Workspace Management

| Command | Description |
|---------|-------------|
| `seja workspace add <path>` | Register a workspace mount point |
| `seja workspace remove <path>` | Remove a workspace mount |
| `seja workspace list` | List registered workspaces |
| `seja workspace sync <path>` | Force markdown-to-SQLite sync |

#### Configuration

| Command | Description |
|---------|-------------|
| `seja config get <key>` | Get a configuration value |
| `seja config set <key> <value>` | Set a configuration value |
| `seja config list` | List all configuration |
| `seja config edit` | Edit configuration in `$EDITOR` |

#### Maintenance

| Command | Description |
|---------|-------------|
| `seja doctor` | Run full diagnostics (Docker, MCP, cosign, git, disk, ports) |
| `seja backup` | Trigger manual Litestream snapshot |
| `seja restore <snapshot>` | Restore from a Litestream snapshot |
| `seja verify` | Run integrity check on SQLite database |

#### Experiments

| Command | Description |
|---------|-------------|
| `seja exp list` | List active experiments |
| `seja exp fork <name>` | Create a new experiment (git worktree + lock) |
| `seja exp merge <name>` | Merge experiment back to main branch |
| `seja exp status [name]` | Show experiment status |
| `seja exp discard <name>` | Discard experiment (remove worktree + branch) |

#### Special

| Command | Description |
|---------|-------------|
| `seja inspect` | Semiotic inspection report on current workspace |
| `seja check` | Run all checkers (constitution, design, plan D16, tests) |
| `seja completion [bash\|zsh]` | Generate shell completion scripts |

### Workspace Lifecycle

```bash
# 1. Initialize a project
cd ~/projects/my-web-app
seja init

# 2. Edit constitution and design intent
$EDITOR .seja/constitution.md
$EDITOR .seja/product-design-as-intended.md

# 3. The FSM will be in 'setup' state.
#    Call the MCP tool to transition:
#    seja.lifecycle.transition_phase("design")

# 4. Work through the lifecycle:
#    design → research → plan → implement → check → document → reflect
```

### Update Flow

```bash
# Check for updates without applying
seja update --check

# Apply update
seja update
# 1. Verifies cosign signature on latest image
# 2. Pulls the new image
# 3. Extracts new CLI script + docker-compose.yml from image
# 4. Compares SHA with current versions
# 5. Replaces atomically with backup
# 6. Restarts services with --force-recreate
```

### Config Reference

| Key | Default | Description |
|-----|---------|-------------|
| `SEJA_IMAGE` | `ghcr.io/puc-behring-institute-for-ai/seja:latest` | Docker image |
| `SEJA_MCP_PORT` | `8765` | MCP server port |
| `SEJA_OPENCODE_PORT` | `4096` | OpenCode port |
| `SEJA_TIER_REASON` | `anthropic/claude-opus-4-5` | Model for reasoning agents |
| `SEJA_TIER_CODE` | `anthropic/claude-sonnet-4-5` | Model for coding agents |
| `SEJA_TIER_FAST` | `anthropic/claude-haiku-4-5` | Model for fast agents |
| `SEJA_BACKUP_S3_BUCKET` | _(none)_ | S3 bucket for Litestream backups |
| `SEJA_BACKUP_S3_REGION` | `us-east-1` | S3 region |
| `LITESTREAM_REPLICA_URL` | `file:///data/replica` | Litestream replica URL |
| `SEJA_DB_PATH` | `/root/.seja-state/seja.db` | SQLite database path |

---

## Agent System

### Tier Model

| Tier | Model | Agents | Purpose |
|------|-------|--------|---------|
| **REASON** | `claude-opus-4-5` | strategy, architect, check, council, semiotic, oracle, research | Deep reasoning, architecture, governance |
| **CODE** | `claude-sonnet-4-5` | planner, implement | Plan generation, code implementation |
| **FAST** | `claude-haiku-4-5` | triage, tester, docs, brief, workspace, boost, chronicler | Quick tasks, test writing, documentation |

### Primary Agents (5)

| Agent | Role | Tab-automatic? | Shell access | Write access |
|-------|------|---------------|-------------|-------------|
| **seja-strategy** | Defines product vision, metacommunication strategy, high-level intent | Yes | Read-only | `.seja/constitution.md`, `.seja/product-design-as-intended.md` |
| **seja-architect** | Translates strategy into feature architecture, validates design decisions | Yes | Read-only | `.seja/designs/` |
| **seja-planner** | Produces D16-structured execution plans from architectural decisions | Yes | `git *`, `npm *` | `.seja/plans/` |
| **seja-implement** | Executes plan steps: codes features, writes tests, updates design docs | Yes | `git add/commit/status/diff/log/branch/merge/worktree`, `npm *`, `rm -f`, `mv` | All workspace files |
| **seja-check** | Runs checkers, validates D16 step completion, verifies invariants | Yes | Read-only | Read-only |

### Hidden Agents (11)

| Agent | Role | Trigger |
|-------|------|---------|
| **seja-triage** | Initial triage: classifies user request, routes to correct agent | First message analysis |
| **seja-tester** | Writes and updates test files following AAA pattern | `/seja-test` or plan step requires test |
| **seja-docs** | Maintains documentation files | `/seja-docs` |
| **seja-research** | Gathers external information, technical research | `/seja-research` |
| **seja-brief** | Creates session briefs and transition summaries | Phase transitions |
| **seja-council** | Multi-architype debate for complex decisions | `/seja-council` |
| **seja-semiotic** | Performs semiotic inspection | `/seja-semiotic` |
| **seja-workspace** | Manages workspace configuration | `/seja-workspace` |
| **seja-boost** | Handles urgent/fast operations | `/seja-boost` |
| **seja-oracle** | Root cause analysis and debugging | `/seja-debug` |
| **seja-chronicler** | Maintains project narrative and changelog | Phase completion |

### Bash Allow-Lists

Each agent template declares explicit `bash.allow` and `bash.deny` lists. Key constraints:

- **No `git push`** on any agent — pushes only via CLI or CI/CD
- **No `git *` wildcards** — only specific commands per role
- **Write scope bounded** to workspace files — no system file modification
- **REASON-tier agents** are read-only — observe, never modify

---

## Lifecycle FSM

### States and Transitions

| # | From | To | Guard | Type |
|---|------|----|-------|------|
| 1 | setup | design | constitution_not_empty | forward |
| 2 | design | research | design_intent_defined | forward |
| 3 | research | plan | research_recommendation_clear | forward |
| 4 | plan | implement | plan_approved | forward |
| 5 | implement | check | all_steps_done | forward |
| 6 | check | document | all_checks_passed | forward |
| 7 | document | reflect | documentation_generated | forward |
| 8 | reflect | design | _(none)_ | cycle |
| 9 | implement | design | reason_provided | reverse |
| 10 | implement | research | reason_provided | reverse |
| 11 | implement | plan | reason_provided | reverse |
| 12 | plan | design | reason_provided | reverse |
| 13 | plan | research | reason_provided | reverse |
| 14 | design | setup | reason_provided | reverse |
| 15 | research | design | reason_provided | reverse |
| 16 | research | setup | reason_provided | reverse |
| 17 | check | implement | reason_provided | reverse |
| 18 | check | plan | reason_provided | reverse |
| 19 | document | check | reason_provided | reverse |
| — | Any | Any | force=true | force |

### Guard Logic

Guards are methods on the FSM class that query the SQLite database through an injected context:

| Guard | Logic | Queries |
|-------|-------|---------|
| `constitution_not_empty` | Projects table has a constitution | `SELECT COUNT(*) FROM constitution_principles` |
| `design_intent_defined` | At least one feature exists | `SELECT COUNT(*) FROM features` |
| `research_recommendation_clear` | Research exists with recommendation | `SELECT COUNT(*) FROM research_reports WHERE recommendation IS NOT NULL` |
| `plan_approved` | Latest plan status = 'approved' | `SELECT status FROM plans ORDER BY created_at DESC LIMIT 1` |
| `all_steps_done` | Zero plan_steps with status != 'done' | `SELECT COUNT(*) FROM plan_steps JOIN plans ... WHERE status != 'done'` |
| `all_checks_passed` | All checker steps completed | `SELECT COUNT(*) FROM plan_steps WHERE checker = 1 AND checker_done_at IS NULL` |
| `documentation_generated` | Documentation for current phase exists | `SELECT COUNT(*) FROM briefs WHERE phase = current_phase` |
| `reason_provided` | `reason` parameter is non-empty | Context check: `bool(self.context.get("reason"))` |

### Force Transition

Any state can transition to any other state using `force=true`. This is a human override — requires an explicit `reason` parameter that is logged to `lifecycle_history`.

```python
# Normal transition
await mcp.call("seja.lifecycle.transition_phase",
    new_phase="implement",
    reason="")

# Reverse transition with reason
await mcp.call("seja.lifecycle.transition_phase",
    new_phase="design",
    reason="Architectural flaw discovered in implementation")

# Force transition
await mcp.call("seja.lifecycle.transition_phase",
    new_phase="check",
    force=true,
    reason="Emergency: production bug requires immediate validation")
```

---

## MCP Server

### Connection Details

| Parameter | Value |
|-----------|-------|
| Server URL | `http://localhost:8765` |
| Transport | `streamable-http` |
| Auth | None (localhost-only by default) |
| Tools registered | 64 |

### Module List

| Module | File | Tools | Key Operations |
|--------|------|-------|----------------|
| **project** | `modules/project.py` | 4 | init, get, detect, status |
| **constitution** | `modules/constitution.py` | 4 | get, get_principle, list, check_compliance |
| **decisions** | `modules/decisions.py` | 6 | create, get, list, search, export, digest |
| **design** | `modules/design.py` | 6 | metacomm, feature CRUD, diff int/as-coded |
| **lifecycle** | `modules/lifecycle.py` | 5 | phase, transition, history, diagram, validate |
| **pending** | `modules/pending.py` | 4 | list, add, resolve, blocking |
| **briefs** | `modules/briefs.py` | 3 | log_started, log_done, recent |
| **telemetry** | `modules/telemetry.py` | 4 | record, query, anomalies, rotate |
| **plans** | `modules/plans.py` | 7 | create, get, list, approve, step update, checker, last approved |
| **research** | `modules/research.py` | 3 | create, get, list |
| **perspectives** | `modules/perspectives.py` | 2 | for_plan, get_perspective |
| **journeys** | `modules/journeys.py` | 4 | create, get, list, semiotic_report |
| **tests** | `modules/tests.py` | 3 | record, results, summary |
| **experiments** | `modules/experiments.py` | 6 | fork, list, status, compare, merge, discard |
| **workspace** | `modules/workspace.py` | 3 | sync, validate, info |

### Key Invariants

These tools are architecturally forbidden (enforced by invariant tests):

| Forbidden Tool | Why |
|---------------|-----|
| `seja.constitution.write` | Constitution is read-only by agents; edited by human |
| `seja.decisions.edit` | Decisions are append-only; corrections create new decision with supersedes |
| `seja.decisions.delete` | Decisions are immutable; supersession is the only operation |
| `seja.briefs.delete` | Briefs are append-only audit log |

### API Contract

All MCP tools accept keyword arguments and return JSON with this envelope:

```json
{
  "success": true,
  "data": { ... },
  "_exported": true,
  "meta": {
    "workspace_path": "/path/to/project",
    "module": "decisions",
    "tool": "create_decision",
    "timestamp": "2026-06-20T15:30:00Z"
  }
}
```

---

## Security

### 5-Layer Defense

```mermaid
graph TB
    L1[Layer 1: Agent Frontmatter] --> L2
    L2[Layer 2: MCP Invariants] --> L3
    L3[Layer 3: Docker Socket Proxy] --> L4
    L4[Layer 4: Container Hardening] --> L5
    L5[Layer 5: Cosign Signing]

    L1 -.- A1[bash.allow explicit lists<br/>no git push<br/>write scope bounded]
    L2 -.- A2[No constitution.write<br/>No decisions.edit/delete<br/>No briefs.delete]
    L3 -.- A3[POST=0, EXEC=0<br/>Only GET + start/stop]
    L4 -.- A4[no-new-privileges<br/>cap_drop ALL + cap_add CHOWN DAC_OVERRIDE<br/>read-only rootfs]
    L5 -.- A5[Cosign keyless OIDC<br/>Container + blob signing<br/>Verification in update flow]
```

### Signature Verification

All SEJA releases are signed with cosign using GitHub OIDC (keyless):

```bash
# Verify container image
cosign verify ghcr.io/puc-behring-institute-for-ai/seja:latest \
  --certificate-identity "https://github.com/PUC-Behring-Institute-for-AI/seja/.github/workflows/publish.yml@refs/tags/v*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

# Verify CLI script
cosign verify-blob \
  --certificate-identity "https://github.com/PUC-Behring-Institute-for-AI/seja/.github/workflows/publish.yml@refs/tags/v*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --bundle scripts/seja.sig \
  scripts/seja
```

### Security Invariants (from ARCHITECTURE.md §22)

| # | Invariant | Enforcement |
|---|-----------|-------------|
| I1 | Container runs with `no-new-privileges` | Docker compose `security_opt` |
| I2 | Only CHOWN + DAC_OVERRIDE capabilities added | Docker compose `cap_add` |
| I3 | Docker socket access goes through proxy only | `socket-proxy` service |
| I4 | Socket proxy blocks POST except start/stop | `POST=0, ALLOW_START=1, ALLOW_STOP=1` |
| I5 | Agents never see `git push` in allow-lists | Frontmatter `bash.allow` |
| I6 | MCP never registers write/delete on constitution, edit/delete on decisions, delete on briefs | Invariant tests (AST-level check) |
| I7 | Cosign signature verified before update | `seja update` flow |
| I8 | Dual-write: SQLite canonical, Markdown derived | Export after every write |

---

## Development

### Local Setup

```bash
git clone https://github.com/PUC-Behring-Institute-for-AI/seja.git
cd seja

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -e mcp/[dev]

# Install dev extras
make install-dev
```

### Running Tests

```bash
# All tests
make test

# Individual suites
make test-unit       # 11 FSM tests
make test-integration # 10 schema integration tests
make test-invariants  # 20 invariant tests (critical - verify forbidden tools)
```

| Suite | File | Tests | What it covers |
|-------|------|-------|----------------|
| **Unit** | `tests/unit/test_fsm.py` | 11 | FSM initial state, forward transitions (blocked/allowed), reverse transitions (requires reason), force, guard conditions |
| **Integration** | `tests/integration/test_schema.py` | 10 | All 18 tables exist, FTS5, WAL mode, foreign keys, roundtrips (project, principle, decision FTS sync, lifecycle, brief), UNIQUE constraints |
| **Invariants** | `tests/invariants/test_invariants.py` | 20 | No forbidden tools registered (AST parsing), tool naming convention, FSM 8 states + 19 transitions, no `git push` in any `.tpl`, cosign.pub PEM format, `_skip_export` logic, module boundary checks |

### CI/CD Pipeline

```mermaid
graph LR
    subgraph "push/PR to main"
        A[validate]
    end
    subgraph "tag v*"
        B[build-and-publish]
    end
    subgraph "scheduled"
        C[security-scan]
    end

    A -->|pass| B
    A --> C
    B --> C

    A -.- L[lint + typecheck + test + invariants + coverage]
    B -.- P[multi-platform build<br/>cosign keyless sign<br/>SBOM + GH Release]
    C -.- S[trivy fs + image scan<br/>SARIF upload]
```

```bash
# Build image locally
make build

# Run full pipeline
make release    # test → build → sign → push → sign-blob
```

### Makefile Targets (24)

| Target | Description |
|--------|-------------|
| `build` | Build Docker image (multi-platform) |
| `build-local` | Build single-arch dev image (fast, no buildx) |
| `test-local` | Build + start + await health + show logs |
| `push` | Push image to GHCR |
| `sign` | Sign image with cosign (keyless) |
| `sign-blob` | Sign CLI script with cosign |
| `verify` | Verify cosign signature |
| `test` | Run all test suites |
| `test-unit` | Run unit tests only |
| `test-integration` | Run integration tests only |
| `test-invariants` | Run invariant tests only |
| `lint` | Run ruff linter |
| `typecheck` | Run mypy |
| `format` | Run ruff formatter |
| `clean` | Clean Python cache files |
| `install-dev` | Install dev dependencies |
| `install` | Install production dependencies |
| `image` | Build image (alias for build) |
| `validate` | Lint + typecheck + test |
| `release` | Full release pipeline |
| `changelog` | Generate changelog from git log |
| `version` | Show current version |
| `security-scan` | Run trivy or grype |
| `help` | Show all targets |

### Local Development Workflow

Test changes locally before committing to save CI iteration time:

```bash
# 1. Build fast single-arch image and test container health
make test-local

# 2. If healthy, lint and run test suites
make validate

# 3. If all pass, commit and push
git add -A && git commit -m "fix: ..."
git push origin main

# 4. Tag for release (triggers CI multi-arch build + GHCR push)
git tag v2.1.6
git push origin v2.1.6
```

The `make test-local` target builds a single-arch image (`seja:dev`), starts the container with `docker compose`, waits 15s for the healthcheck, and reports the container status. If unhealthy, it shows the last 30 log lines for diagnosis.

To manually inspect a local build:

```bash
# Build dev image
make build-local

# Start with local image
SEJA_IMAGE=seja:dev docker compose up -d

# Watch health
docker compose logs -f seja

# Stop when done
docker compose down
```

---

## Reference

| Resource | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Complete architectural specification (3748 lines, 23 sections) |
| [AGENTS.md.global](opencode/AGENTS.md.global) | Global SEJA governance framework for OpenCode |
| [Agent templates](opencode/agents/) | 16 agent `.md.tpl` files with envsubst variable injection |
| [Custom commands](opencode/commands/) | 13 `/seja-*` command definitions |
| [OpenCode config](opencode/opencode.json.tpl) | MCP server URL, agent model assignments, plugins, providers |
| [Project templates](project-template/.seja/) | `.seja/` scaffold: constitution, decisions, plans, designs, briefs |
| [Docker Compose](docker-compose.yml) | 3-service compose file (seja, socket-proxy, litestream) |
| [Makefile](Makefile) | 22 targets: build, test, lint, release |
| [MCP modules](mcp/seja_mcp/modules/) | 15 MCP tool modules (decisions, lifecycle, plans, etc.) |
| [Test suites](tests/) | Unit (FSM) + Integration (schema) + Invariants (security) |

### Bibliography

- de Souza, C. S. (2005). *The Semiotic Engineering of Human-Computer Interaction*. MIT Press.
- de Souza, C. S., & Leitão, C. F. (2009). *Semiotic Engineering Methods for Scientific Research in HCI*. Morgan & Claypool.
- Norman, D. A. (2013). *The Design of Everyday Things*. Basic Books. (Conceptual model alignment, metacommunication)

---

## Troubleshooting

### Docker: command not found or permission denied

```bash
# Check Docker is running
docker info

# Permission denied? Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# macOS: ensure Docker Desktop is running (menu bar icon)
# Windows: ensure WSL2 integration is enabled in Docker Desktop settings
```

**Root cause:** SEJA requires a running Docker daemon with socket access. The container uses a socket-proxy with ACL — it never accesses the socket directly.

---

### Port conflict (8765 or 4096 already in use)

```bash
# Check what is using the port
lsof -i :8765
lsof -i :4096

# Change SEJA ports via .env
echo "SEJA_MCP_PORT=18765" >> ~/.seja/.env
echo "SEJA_OPENCODE_PORT=14096" >> ~/.seja/.env
seja restart
```

**Root cause:** SEJA binds ports 8765 (MCP) and 4096 (OpenCode) on the host. If another service uses these ports, change them in `~/.seja/.env` before starting.

---

### Container starts but never becomes healthy

```bash
# Error: "Timeout waiting for seja to become healthy"
# Root cause: the MCP server failed to start inside the container

# 1. Check container logs
seja logs seja --tail 30

# 2. Common failure: missing database migration module
#    Error: "ModuleNotFoundError: No module named 'seja_mcp.db.migrate'"
#    Fix: update to SEJA v2.1.5+ (this bug was fixed)

# 3. Check if the container is running at all
docker ps -a --filter name=seja

# 4. If the container exited, inspect the exit code
docker inspect seja --format 'ExitCode: {{.State.ExitCode}} / {{.State.Status}}'

# 5. Try restarting
seja restart
```

**Root cause:** The container entrypoint runs database migrations then starts the MCP server on port 8765. If either step fails (missing module, corrupt database, port conflict), the container starts but healthcheck never succeeds because the health endpoint is not listening.

**Diagnostic flow:**
```
seja start
  → Container starts
  → Entrypoint runs migrations (python -m seja_mcp.db.migrate)
  → Entrypoint renders agent templates (envsubst)
  → Entrypoint starts MCP server (python -m seja_mcp.server)
  → MCP server listens on :8765/health
  → Docker healthcheck: curl -f http://localhost:8765/health
  → "healthy"
```

If any step fails, `seja logs seja` will show the error.

---

### `seja setup` fails with image pull error

```bash
# Retry with verbose output
seja setup --no-pull

# Then pull manually
docker pull ghcr.io/puc-behring-institute-for-ai/seja:latest

# Check GitHub Packages authentication
echo $GITHUB_TOKEN  # Set if pulling from private registry
```

**Root cause:** GHCR images require authentication for some configurations. If behind a corporate proxy, configure `~/.docker/config.json` or set `$DOCKER_CONFIG`.

---

### MCP server not responding (`seja status` shows unhealthy)

```bash
# Check container logs
seja logs seja --tail 50

# Verify the MCP server started
seja exec curl -f http://localhost:8765/health

# Check if migrations ran
seja exec ls -la /root/.seja-state/seja.db

# Restart services
seja restart
```

**Common causes:**
- First startup: migrations need a few seconds — wait 10s and retry
- Disk full: `seja doctor` reports disk space
- Corrupted database: `seja verify` checks integrity; `seja restore` can recover
- Socket proxy not ready: `seja logs socket-proxy` for connection errors

---

### `seja update` fails with signature verification error

```bash
# Check current cosign public key
cat ~/.seja/cosign.pub

# Re-download the public key
curl -fsSL -o ~/.seja/cosign.pub \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/cosign.pub"

# Manual cosign verification
cosign verify ghcr.io/puc-behring-institute-for-ai/seja:latest \
  --certificate-identity "https://github.com/PUC-Behring-Institute-for-AI/seja/.github/workflows/publish.yml@refs/tags/v*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

**Root cause:** SEJA uses cosign keyless signing (GitHub OIDC). The certificate identity must match the exact workflow path and tag pattern. If the public key file is outdated, re-download it.

---

### Litestream replica errors

```bash
# Check litestream logs
seja logs litestream --tail 20

# Default (local) replica works out of the box
# For S3: verify credentials in ~/.seja/.env
grep SEJA_BACKUP_S3 ~/.seja/.env
```

**Root cause:** Default replica URL is `file:///data/replica` (local, works without configuration). S3 requires `SEJA_BACKUP_S3_BUCKET` and AWS credentials. See [S3 Backup Configuration](#s3-backup-configuration).

---

### Workspace not found

```bash
# List registered workspaces
seja workspace list

# Add a workspace
seja workspace add /path/to/project

# Verify workspace
ls /path/to/project/.seja/  # Should contain constitution, designs/, etc.
```

**Root cause:** Each project must be initialized with `seja init` or added via `seja workspace add`. The container mounts workspaces via `docker-compose.override.yml` — workspaces not registered are invisible inside the container.

---

### Agent reports "permission denied" or "tool not available"

```
# Example error from agent
"Error: bash command 'git push' is not in the allow-list for this agent"
```

**This is expected by design.** SEJA enforces agent capabilities via `bash.allow` lists:
- **REASON-tier agents** (strategy, architect, check, council, etc.) are read-only — they observe and recommend, never modify.
- **`git push` is denied for all agents** — pushes happen only via CI/CD or manual CLI.
- **REASON and CODE agents** have scoped write access: only workspace files, never system files.

To give an agent access to a specific command, modify its `.md.tpl` file in `opencode/agents/`.

---

### Container exits immediately

```bash
# Check exit code
docker inspect seja --format '{{.State.ExitCode}}'

# View exit logs
seja logs seja --tail 30
```

**Common causes:**
- Entrypoint script error: check `Docker/entrypoint.sh` in the source repo
- Missing environment variables: verify `~/.seja/.env`
- Port already in use inside container: rare, restart usually resolves

---

### Permission denied writing to `/usr/local/bin/seja`

```bash
# Error: "Failure writing output to destination" or "Permission denied"
# Root cause: /usr/local/bin is owned by root; write requires sudo

# Fix: run curl with sudo
sudo curl -fsSL -o /usr/local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/seja"
sudo chmod +x /usr/local/bin/seja

# Alternative: install to ~/.local/bin (no sudo needed)
mkdir -p ~/.local/bin
curl -fsSL -o ~/.local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/seja"
chmod +x ~/.local/bin/seja
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### `seja` CLI script not found after install

```bash
# Reinstall with sudo
sudo curl -fsSL -o /usr/local/bin/seja \
  "https://github.com/PUC-Behring-Institute-for-AI/seja/releases/latest/download/seja"
sudo chmod +x /usr/local/bin/seja

# Or if installed to ~/.local/bin, ensure it's on PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

---

## FAQ

### Do I need an Anthropic API key?

**Yes.** SEJA uses OpenCode as the agent runtime, which requires an Anthropic API key. Set it as an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

You can also add it to `~/.seja/.env` for persistence:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> ~/.seja/.env
```

Get an API key at [console.anthropic.com](https://console.anthropic.com).

---

### Can I use models other than Claude?

**Yes.** SEJA supports any model provider that OpenCode supports (OpenAI, Google, AWS Bedrock, etc.). Change the tier models in `.env`:

```bash
echo 'SEJA_TIER_REASON=openai/gpt-4o' >> ~/.seja/.env
echo 'SEJA_TIER_CODE=openai/gpt-4o-mini' >> ~/.seja/.env
echo 'SEJA_TIER_FAST=openai/gpt-4o-mini' >> ~/.seja/.env
```

Format: `<provider>/<model>` (OpenCode model identifier). The corresponding API key (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.) must be set.

---

### Does SEJA need a GPU?

**No.** SEJA is CPU-only. The agent runtime calls external LLM APIs — all computation happens on the API provider's servers.

---

### How do I make backups?

**Automatic:** Litestream replicates the SQLite database continuously:

```bash
# Local replica (default, no config needed)
# Replicas stored in ~/.seja/backups/litestream/

# Manual snapshot
seja backup

# List available snapshots
ls ~/.seja/backups/litestream/
```

**S3 backup:** See [S3 Backup Configuration](#s3-backup-configuration).

**Restore:**
```bash
seja restore <snapshot-path>
```

---

### How do I completely uninstall SEJA?

```bash
# 1. Stop services
seja stop

# 2. Remove runtime directory
rm -rf ~/.seja

# 3. Remove the CLI binary
rm /usr/local/bin/seja

# 4. (Optional) Remove Docker images
docker rmi ghcr.io/puc-behring-institute-for-ai/seja:latest

# 5. (Optional) Remove Docker volumes
docker volume rm seja_seja-state seja_seja-home seja_socket-proxy seja_litestream-data
```

---

### Is SEJA compatible with macOS and Windows?

- **macOS:** ✅ Fully supported via Docker Desktop. Tested on macOS 14+ (Sonoma/Sequoia).
- **Windows:** ✅ Supported via WSL2 with Docker Desktop WSL2 backend. Run all SEJA commands inside the WSL2 distribution.
- **Linux:** ✅ Native support. Tested on Ubuntu 22.04+ and Debian 12+.

The `seja` CLI script is tested on Bash 4+ (macOS pre-installed Bash is version 3 — install via Homebrew if needed: `brew install bash`).

---

### How many agents run at the same time?

**One at a time.** OpenCode uses a tab-based interface where agents are invoked sequentially. The SEJA agent system has 16 agents, but only one is active per conversation turn (tab-automatic agents activate based on context). Hidden agents (`/seja-*` commands) run on demand.

---

### How do I change the ports SEJA uses?

Edit `~/.seja/.env`:

```bash
SEJA_MCP_PORT=18765       # Default: 8765
SEJA_OPENCODE_PORT=14096   # Default: 4096
```

Then restart:
```bash
seja restart
```

---

### Can I use SEJA without OpenCode?

**Not recommended.** SEJA's governance layer (agent templates, FSM lifecycle, MCP tools) is designed specifically for the OpenCode agent runtime. While the MCP server could technically work with any MCP-compatible client (like Claude Desktop), the agent governance system, lifecycle FSM, and bash allow-lists are OpenCode-specific.

---

## S3 Backup Configuration

Litestream can replicate SQLite WAL changes to S3-compatible storage for disaster recovery.

### Minimal S3 Setup

```bash
# 1. Create an S3 bucket (AWS CLI example)
aws s3 mb s3://seja-backups --region us-east-1

# 2. Add lifecycle policy for cost management
aws s3api put-bucket-lifecycle-configuration \
  --bucket seja-backups \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-old-backups",
      "Status": "Enabled",
      "Expiration": { "Days": 90 },
      "Filter": {}
    }]
  }'

# 3. Create IAM user with programmatic access and this policy:
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
#       "Resource": ["arn:aws:s3:::seja-backups", "arn:aws:s3:::seja-backups/*"]
#     }
#   ]
# }
```

### Configure SEJA

Add these to `~/.seja/.env`:

```bash
SEJA_BACKUP_S3_BUCKET=seja-backups
SEJA_BACKUP_S3_REGION=us-east-1
SEJA_BACKUP_S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
SEJA_BACKUP_S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### Verify replication

```bash
# Restart to pick up S3 config
seja restart

# Check litestream logs for successful replication
seja logs litestream --tail 10

# Expected output:
# "litestream: replicate: snapshot created" (every 10 minutes by default)

# List S3 snapshots
aws s3 ls s3://seja-backups/
```

### Restore from S3

```bash
# Stop services first
seja stop

# List available snapshots
aws s3 ls s3://seja-backups/

# Restore
seja restore s3://seja-backups/<snapshot-path>
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
