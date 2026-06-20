# Experiments

Registro de experimentos de exploração paralela (worktrees com lifecycle).

Cada experimento é um fork isolado em worktree git com branch nomeado
`exp/<name>-<date>`, lock automático, e mini-FSM próprio:

```
fork → active → ready → merged
                   └→ discarded
```

- Experimentos permitem explorar abordagens concorrentes sem contaminar o tronco.
- O `seja-council` compara experimentos e produz ranking.
- O `seja-semiotic-inspector` avalia spec-drift de cada experimento.
