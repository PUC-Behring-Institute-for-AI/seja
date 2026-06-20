# Briefs

Registro cronológico de invocações de agentes (append-only).

- **Formato:** `STARTED | timestamp | agente | descrição`
- **Imutabilidade:** ferramentas de edição/deleção NÃO EXISTEM no MCP
- **Uso:** auditoria, diagnóstico, telemetria

O brief log é a fonte primária para entender o que cada agente fez,
em que ordem, e por quanto tempo. É exportado para `_output/briefs.md`
e também armazenado no SQLite.
