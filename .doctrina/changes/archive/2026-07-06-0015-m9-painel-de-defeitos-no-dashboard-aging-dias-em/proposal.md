# Change 0015-m9-painel-de-defeitos-no-dashboard-aging-dias-em — M9 painel de defeitos no dashboard: aging (dias em aberto), por severidade e por squad; defeito ganha campo opened (data), report GET /metrics/defects, e painel no dashboard respeitando o filtro de squad

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** defects

## Why

M9 painel de defeitos no dashboard: aging (dias em aberto), por severidade e por squad; defeito ganha campo opened (data), report GET /metrics/defects, e painel no dashboard respeitando o filtro de squad

## What

- **indexer.py** — coluna `opened_at` em defects (migração tolerante); `_insert_defect` indexa `opened`.
- **api.py** — carimba `opened` (data) na criação do defeito; novo `GET /metrics/defects?squad=`.
- **metrics.py** — `defects_report`: defeitos abertos por severidade, por squad (efetivo do CT vinculado) e por faixa de aging (0–7 / 8–30 / 30+), + lista com `age_days`.
- **Frontend** — `DefectsPanel` no dashboard (resumo + tabela), respeitando o filtro de squad; empty state quando não há defeito aberto.
- **Testes** — `test_defects_report_aging_severity_and_squad` e `test_defects_report_empty`.

## Scope boundaries

- Aging usa `opened`; defeitos legados sem data ficam com `age_days: null` (não quebram).
- Squad do defeito é derivado do CT vinculado (não é um campo próprio do defeito).
- Continua sem workflow de bug tracker (ADR/intake): é ponteiro + metadados.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 77 + build do frontend).
- [x] Critérios defects#3 e reporting#7 cobertos por `backend/tests/test_defects.py` (`doctrina coverage`).
- [x] Retrocompat: defeito sem `opened` → age null; painel vazio quando não há defeito.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
