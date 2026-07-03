# Spec — reporting

**Capability:** reporting
**Status:** active
**Implementation:** planned — deferido ao M1.5 (após M1)
**Realizes:** SC3
**Last updated:** 2026-07-03
**Version:** 0.1.0

## Purpose

Dashboard e matriz de rastreabilidade para reporte à gestão — a dor
declarada número um. Métricas escolhidas por serem defensáveis em reunião,
com fórmula explícita, calculadas por queries no índice SQLite. Inclui
export PDF e Markdown (para colar no Confluence).

## Requirements (EARS)

### Ubiquitous

- The system shall calcular as 7 métricas com as fórmulas do intake (§11):
  cobertura de requisito (stories `active` com ≥1 CT `ready` ÷ stories
  `active`), cobertura de execução, pass rate (`passed` ÷ `passed`+`failed`),
  taxa de bloqueio, retrabalho (passaram por `retest` ÷ total),
  instabilidade/flaky (alternância pass/fail em janela N) e tendência
  diária (7/15/30 dias).
- The system shall expor `GET /metrics/summary`, `/metrics/trend`,
  `/metrics/coverage`, `/metrics/traceability`, `/metrics/flaky` com os
  filtros do contrato (sprint, days, epic, window).
- The system shall renderizar a matriz de rastreabilidade
  Epic → Story | CTs | Último resultado | Execution | Evidências |
  Defeitos, com cada célula clicável até o arquivo de evidência
  (drill-down completo).
- The system shall marcar stories sem CT como "sem cobertura" na matriz.
- The system shall exportar a matriz em PDF e em Markdown.

### Event-driven

- When o usuário aplica filtro de epic ou sprint, the system shall
  recalcular matriz e métricas sobre o subconjunto filtrado.

### State-driven

- While não há dados de execução no período, the system shall exibir
  métricas zeradas com denominadores explícitos (nunca esconder a fórmula).

### Unwanted-behavior (must-not)

- The system shall not contabilizar resultados não-finais (`pending`,
  `in_progress`) no pass rate.
- The system shall not usar cor como único indicador de status (sempre
  ponto colorido + texto).

### Optional

- Where a janela de flaky N é configurada, the system may recalcular a
  instabilidade sobre as últimas N execuções.

## Acceptance criteria

1. [unverified] Reporte de sprint gerado em < 1 minuto com drill-down até
   evidência — verified by `tests/test_reporting_e2e.py`.
2. [unverified] Cada métrica bate com a fórmula sobre um dataset fixture
   conhecido — verified by `tests/test_metrics.py`.
3. [unverified] Export Markdown da matriz é colável no Confluence sem
   perda de estrutura — verified by `tests/test_export.py`.
4. [unverified] Export PDF gerado com a matriz navegada — verified by
   `tests/test_export.py`.

## Maturity

**MVP (committed):**

- 7 métricas, tendência, matriz navegável, export PDF/MD.

**Future (aspirational, not committed):**

- Comparação entre sprints; metas/thresholds configuráveis por métrica.

## Out of scope for this spec

- Coleta dos dados (ver `executions`, `indexing`).
