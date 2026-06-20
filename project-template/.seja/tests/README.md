# Test Results

Registro de execuções de teste vinculadas a planos e steps.

- **Formato:** `test-<uuid[:8]>` (no SQLite, exportado para markdown)
- **Outcomes:** `passed` | `failed` | `skipped` | `error`
- **Vínculo:** cada teste pertence a um plano e opcionalmente a um step

O `seja-test-runner` registra execuções via `seja.tests.record_test_run()`.
O guard `required_tests_passed` do FSM bloqueia transição check → document
se houver testes failed.
