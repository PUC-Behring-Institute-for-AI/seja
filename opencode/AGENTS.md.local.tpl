# AGENTS.md — [NOME_DO_PROJETO] (camada local)
# Location: <projeto-root>/AGENTS.md
# Inherits: ~/.config/opencode/AGENTS.md (SEJA Governance Framework — global rules)
# Requires: global >= 2.1.0
# Overrides or extends only what is listed below.

## Project

- **Name:** [NOME_DO_PROJETO]
- **Description:** [Uma frase de descrição]
- **Stack:** [linguagem, framework, runtime, package manager]
- **Workspace:** /workspace/[NOME_DO_PROJETO]

## Model configuration

**PLANNER:** ${SEJA_TIER_REASON} — responsible for plans and architecture decisions
**EXECUTOR:** ${SEJA_TIER_CODE} — responsible for implementation only
**PLANNER subagent:** @seja-planner | **EXECUTOR subagent:** @seja-implement

## Phase override

<!-- Remove if inheriting lifecycle phase from workspace state -->

**Fase Atual do Lifecycle:** [FASE]
Última transição em: [DATA]

## Routing overrides

<!-- Routes added on top of the global routing model. -->

| Pattern | Route to |
|---------|----------|
| [domain/task pattern] | [agent name] |

## Project-specific axiom constraints

<!-- These add to the global axioms (Section 4). They NEVER relax global axioms. -->

- [Axiom constraint 1]
- [Axiom constraint 2]

## Stack standards

| Concern | Standard |
|---------|----------|
| Language version | [e.g., Python 3.12] |
| Formatting | [e.g., ruff] |
| Linting | [e.g., ruff, mypy] |
| Testing | [e.g., pytest] |
| CI | [e.g., GitHub Actions] |

## Architecture patterns

[Active patterns, e.g., "Layered: api / service / repository / domain"]
[Or "none decided yet"]

## Document lifecycle

| Document | Status | Created when |
|----------|--------|-------------|
| `.seja/constitution.md` | pending | First /seja-setup run |
| `.seja/conventions.md` | pending | First /seja-setup run |
| `.seja/product-design-as-intended.md` | pending | First design session |
| `.seja/product-design-as-coded.md` | pending | First implementation step |
| `.seja/decisions/D-NNN.md` | pending | First decision recorded |

## Exit criteria for current phase

<!-- Ver catálogo completo: Seção 17 do ARCHITECTURE.md -->

- [ ] Gate 1: [descrição] — **HARD** — o sistema bloqueia
- [ ] Gate 2: [descrição] — advisory — o harness recomenda

## Quick references

- Design intent: `.seja/product-design-as-intended.md`
- State as-coded: `.seja/product-design-as-coded.md`
- Decisions: `.seja/decisions/`
- Journey maps: `.seja/journeys/`
- Plans: `.seja/plans/`
- Research: `.seja/research/`
- Pending: `/seja-status` or `seja.pending.list_pending()`
- Telemetry & briefs: `.seja/_output/`
