# Spec — reporting

**Capability:** reporting
**Status:** active
**Implementation:** verified — M1.5 + M7 (filtro squad) + M8 (metas/thresholds); backend/arbites/metrics.py, backend/arbites/api.py, backend/arbites/export_pdf.py, frontend/src/components/Dashboard.tsx
**Realizes:** SC3
**Last updated:** 2026-07-06
**Version:** 0.4.0

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
- The system shall calcular a tendência diária contando cada par
  (execução, testcase) **uma vez por dia**, pelo status da última
  transição registrada naquele dia — nunca somando transições
  intermediárias.
- The system shall expor `GET /metrics/summary`, `/metrics/trend`,
  `/metrics/coverage`, `/metrics/traceability`, `/metrics/flaky` com os
  filtros do contrato (sprint, days, epic, window).
- The system shall renderizar a matriz de rastreabilidade
  Epic → Story | CTs | Último resultado | Execution | Evidências |
  Defeitos, com cada célula clicável até o arquivo de evidência
  (drill-down completo).
- The system shall marcar stories sem CT como "sem cobertura" na matriz.
- The system shall exportar a matriz em PDF e em Markdown.
- The system shall anotar cada métrica do summary com um `status`
  (ok/warn/bad/none) contra metas opcionais configuradas em `arbites.yaml`
  (`metric_thresholds`), respeitando a direção da métrica (maior-melhor ou
  menor-melhor).

### Event-driven

- When o usuário aplica filtro de epic ou sprint, the system shall
  recalcular matriz e métricas sobre o subconjunto filtrado.

### State-driven

- While não há dados de execução no período, the system shall exibir
  métricas zeradas com denominadores explícitos (nunca esconder a fórmula).
- While nenhuma meta está configurada para uma métrica, the system shall
  reportar `status: none` e não colorir o card (número e fórmula seguem
  visíveis).

### Unwanted-behavior (must-not)

- The system shall not contabilizar resultados não-finais (`pending`,
  `in_progress`) no pass rate.
- The system shall not inflar a tendência contabilizando transições
  intermediárias de status: reordenar/re-arrastar um mesmo CT entre
  colunas no mesmo dia não pode aumentar a contagem daquele dia.
- The system shall not usar cor como único indicador de status (sempre
  ponto colorido + texto).

### Optional

- Where a janela de flaky N é configurada, the system may recalcular a
  instabilidade sobre as últimas N execuções.

## Acceptance criteria

1. [verified] Reporte de sprint gerado em < 1 minuto com drill-down até
   evidência — verified by `backend/tests/test_reporting_e2e.py`.
2. [verified] Cada métrica bate com a fórmula sobre um dataset fixture
   conhecido — verified by `backend/tests/test_metrics.py`.
3. [verified] Export Markdown da matriz é colável no Confluence sem
   perda de estrutura — verified by `backend/tests/test_export.py`.
4. [verified] Export PDF gerado com a matriz navegada — verified by
   `backend/tests/test_export.py`.
5. [verified] Um único CT arrastado por vários status no mesmo dia conta
   como 1 no status final do dia na tendência, não como vários — verified
   by `backend/tests/test_metrics.py`.
6. [verified] Cada métrica recebe status ok/warn/bad conforme a meta e a
   direção configuradas, e `none` quando não há meta — verified by
   `backend/tests/test_metrics.py`.

## Maturity

**MVP (committed):**

- 7 métricas, tendência, matriz navegável, export PDF/MD, metas/thresholds
  por métrica (semáforo).

**Future (aspirational, not committed):**

- Comparação entre sprints.

## Out of scope for this spec

- Coleta dos dados (ver `executions`, `indexing`).
