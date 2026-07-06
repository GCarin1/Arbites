---
name: metricas-resultado-liquido
description: Como escrever métricas de reporting sobre o índice sem inflar contagem — distinguir estado atual (results) de log de transições (result_events).
when: Ao adicionar ou alterar qualquer métrica/agrupamento em backend/arbites/metrics.py, ou ao ler/agregar as tabelas results e result_events.
---

# Skill — metricas-resultado-liquido

## When to use this skill

- Vai criar ou alterar uma métrica em `backend/arbites/metrics.py`
  (summary, trend, coverage, flaky, rework, traceability).
- Vai escrever qualquer `SELECT ... COUNT(*)` sobre `results` ou
  `result_events`.
- Está investigando um número "inflado" no Dashboard (parece haver mais
  resultados do que CTs).

## Contexto — duas tabelas, dois significados

O indexador (`backend/arbites/indexer.py`) mantém **duas** projeções dos
resultados de execução, e confundi-las é a causa raiz da inflação:

- **`results`** — *estado atual*. PK `(execution_id, testcase_id)`,
  gravado com `INSERT OR REPLACE`. Exatamente **uma linha por CT por
  execução**, com o `status` corrente. Use para "quantos CTs estão/ficaram
  em X".
- **`result_events`** — *log de transições*. Gravado com `INSERT` puro, uma
  linha por evento `result` do `history[]`. **Cresce a cada arrasto** no
  kanban. Um único CT movido blocked→failed→passed→blocked gera 4 linhas.
  Use para tendência/fluxo temporal, **nunca** para "quantos CTs".

## Procedure

1. Pergunte: a métrica conta **coisas** (CTs, resultados distintos) ou
   **eventos** (fluxo ao longo do tempo)?
2. Conta coisas → parta de **`results`** (já deduplicado pela PK). Ex.:
   `pass_rate`, `blocked_rate`, `execution_coverage` — todos sobre `results`.
3. Precisa mesmo de `result_events` (dimensão temporal) → **deduplique o
   líquido** antes de contar. Pegue a última transição por
   `(execution_id, testcase_id, dia)` e só então agrupe:
   ```sql
   SELECT day, status, COUNT(*) c FROM (
     SELECT substr(v.at,1,10) day, v.status,
       ROW_NUMBER() OVER (
         PARTITION BY v.execution_id, v.testcase_id, substr(v.at,1,10)
         ORDER BY v.at DESC, v.rowid DESC) rn
     FROM result_events v JOIN executions e ON e.id = v.execution_id
     WHERE <cutoff/sprint>
   ) WHERE rn = 1 AND status IN ('passed','failed','blocked')
   GROUP BY day, status
   ```
   (SQLite ≥ 3.25 tem window functions; o `rowid` desempata timestamps iguais.)
4. Reproduza com o cenário do bug antes de fechar: 1 CT arrastado por
   vários status no mesmo dia deve contar **1**, no status final. Teste em
   `backend/tests/test_metrics.py`.

## Anti-patterns

- `COUNT(*)` cru sobre `result_events` para responder "quantos passaram/
  falharam" — conta cada arrasto, não cada CT. Foi o bug 0009.
- Assumir que o `execution.json`/kanban duplica: **não duplica** — o JSON
  guarda 1 resultado por CT. A inflação mora em métricas que leem o log de
  transições.
- Deduplicar por `retest`/`COUNT(DISTINCT exec||tc)` já protege `rework_rate`
  e `flaky`; replique esse cuidado em métricas novas.

## Related material

- [Spec reporting](../specs/reporting/spec.md) — critério SC5 e o
  unwanted-behavior "não inflar a tendência".
- [ADR 0001](../decisions/0001-filesystem-como-fonte-de-verdade-sqlite-como-indice-descartavel.md)
  — SQLite é índice descartável derivado do disco.
- [ADR 0005](../decisions/0005-status-de-documento-separado-de-status-de-resultado.md)
  — máquinas de estado de resultado (as transições que viram eventos).
