# Constituição do Projeto

## Propósito / Missão

<!--
Defina em uma frase a razão de existir deste projeto.
Exemplo: "Este projeto existe para [entregar X a Y], governado pelo SEJA."
-->

**[PREECHER]**

## Princípios Fundamentais

Estes princípios são imutáveis para agentes. Apenas humanos podem alterá-los.
Cada princípio segue a Semiotic Engineering: o sistema deve comunicar fielmente
a intenção do designer ao usuário, sem ruído introduzido por intermediários.

### Princípios Técnicos

| ID | Princípio | Rationale |
|----|-----------|-----------|
| T1 | **[PREECHER]** | **[PREECHER]** |
| T2 | **[PREECHER]** | **[PREECHER]** |
| T3 | **[PREECHER]** | **[PREECHER]** |
| T4 | **[PREECHER]** | **[PREECHER]** |

### Princípios de Qualidade

| ID | Princípio | Rationale |
|----|-----------|-----------|
| Q1 | **[PREECHER]** | **[PREECHER]** |
| Q2 | **[PREECHER]** | **[PREECHER]** |
| Q3 | **[PREECHER]** | **[PREECHER]** |

## Operating Agreements

<!-- Regras de convivência entre agentes e humano. Exemplos:
- Toda implementação requer plano aprovado.
- Nenhum agente edita a constituição.
- Decisões arquiteturais são imutáveis (D-NNN).
-->

- **[PREECHER]**
- **[PREECHER]**
- **[PREECHER]**

## Modelo de Governança

Este projeto é governado pelo SEJA Lifecycle FSM com 8 fases:

```
setup → design → research → plan → implement → check → document → reflect → design
```

Transições são controladas por guards (exit criteria). O humano pode forçar
transições com `force=true` e reason registrado.

Fase atual: **setup**

## Processo de Mudança

1. **Mudança na constituição**: apenas humanos. Ferramenta MCP não existe para agentes.
2. **Mudança de decisão arquitetural**: nova D-NNN com `supersedes` apontando para a anterior.
3. **Mudança de design intent**: atualizar `product-design-as-intended.md` e registrar nova decisão.
4. **Mudança de fase**: via `seja.lifecycle.transition_phase()` com guards e reason.
