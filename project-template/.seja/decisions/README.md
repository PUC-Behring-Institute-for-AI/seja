# Decision Records (D-NNN)

Registro de decisões arquiteturais do projeto, seguindo o formato MADR-alinhado.

- **Formato:** `D-NNN-xxxx.md` (counter atômico + short UUID)
- **Ciclo de vida:** `accepted` → `superseded` (nunca editada ou deletada)
- **Supersession:** uma decisão obsoleta é substituída via `supersedes` na nova decisão
- **Imutabilidade:** ferramentas de edição/deleção NÃO EXISTEM no MCP

Cada decisão contém: Context, Decision, Rationale, Consequences, Alternatives Considered.
