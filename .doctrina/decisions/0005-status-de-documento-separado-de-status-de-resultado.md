# ADR 0005 — Status de documento separado de status de resultado

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de modelo de dados do intake; nenhuma implementação ainda (landará com o M1)
- **Landed:** —

## Context

Erro comum em ferramentas de teste (presente na discussão original do
projeto): misturar o estado do documento de teste com o resultado de uma
execução. O mesmo CT precisa poder estar `passed` na EXEC-0001 e `failed`
na EXEC-0002 sem contradição.

## Decision

Três máquinas de estado independentes: Test Case (documento:
`draft → ready → deprecated`, no frontmatter do `.md`), Resultado (CT
dentro de uma execution: `pending → in_progress →
passed|failed|blocked|retest` + coluna `closed`, no `execution.json`) e
Execution (ciclo: `draft → in_progress → closed`, no `execution.json`). O
Kanban da UI opera sobre resultados dentro de uma execution, nunca sobre o
documento.

## Alternatives considered

1. Ciclo de vida único misto (documento + resultado no mesmo campo) —
   rejeitado: torna impossível o mesmo CT ter resultados diferentes em
   executions diferentes e corrompe o histórico.

## Consequences

**Positive**

- Histórico de execuções íntegro; métricas (pass rate, flaky) calculáveis
  por execution.

**Negative**

- Três máquinas de estado para o usuário entender; mitigado pela UI
  (Kanban só mostra resultados).

**Neutral**

- O documento do CT muda raramente; resultados mudam a cada ciclo.
