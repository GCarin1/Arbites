# Change 0051-fix-heatmap-de-atividade-metrics-activity-heatma — fix: heatmap de atividade (metrics.activity_heatmap) misturava timestamps UTC (result_events.at, executions.created_at) com datas LOCAIS (defects.opened_at, testcases/requirements.created) no mesmo bucket por dia. Em fusos atras de UTC (ex: Brasil, UTC-3), atividade de execucao/automacao de fim de tarde cai no dia UTC seguinte, que fica fora da janela 'ate hoje local' e some do heatmap silenciosamente. Fix: _local_date() converte os dois campos UTC pra data local antes de bucketar; _activity_years tinha o mesmo problema na virada de ano e foi corrigido igual

- **Status:** applied
- **Applied:** 2026-07-12
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** (none — chore)

## Why

fix: heatmap de atividade (metrics.activity_heatmap) misturava timestamps UTC (result_events.at, executions.created_at) com datas LOCAIS (defects.opened_at, testcases/requirements.created) no mesmo bucket por dia. Em fusos atras de UTC (ex: Brasil, UTC-3), atividade de execucao/automacao de fim de tarde cai no dia UTC seguinte, que fica fora da janela 'ate hoje local' e some do heatmap silenciosamente. Fix: _local_date() converte os dois campos UTC pra data local antes de bucketar; _activity_years tinha o mesmo problema na virada de ano e foi corrigido igual

## What

Achado ao rodar `pytest` à noite (horário de Brasília): `test_activity_heatmap_
aggregates_daily_signals` falhava de forma dependente da hora do dia —
`day["executions"] == 0` quando deveria ser 3. Reproduzido com servidor real:
`result_events.at`/`executions.created_at` são carimbados em UTC (`_now()` de
`executions.py`); `defects.opened_at`/`testcases.created`/`requirements.created`
são carimbados com `date.today()` LOCAL. `activity_heatmap` bucketava os dois
juntos sem converter — em fusos atrás de UTC (Brasil, UTC-3), qualquer
atividade de execução/automação a partir do fim da tarde local já é "amanhã"
em UTC, cai FORA da janela "até hoje local" e **some silenciosamente** do
heatmap. Sem exceção, sem log — só o número errado.

- **backend/arbites/metrics.py** — `_local_date(iso)`: converte um timestamp
  UTC-aware para a data local do processo; identidade para uma data local pura
  (sem hora/fuso, como `date.today().isoformat()`). `activity_heatmap` passa
  as duas fontes UTC (`result_events.at`, `executions.created_at`) por ela
  linha a linha antes de bucketar; as três já-locais continuam agregadas
  direto via SQL `GROUP BY` (não têm componente de hora/fuso, nada a converter).
  `_activity_years` recebeu o mesmo fix (virada de ano UTC × local). Removida
  `_ACTIVITY_DATE_EXPRS`, uma tupla morta que nunca era referenciada.
- **backend/tests/test_activity_heatmap.py** — teste de regressão determinístico
  (`_local_date` vs `datetime.fromisoformat(...).astimezone()`), independente
  do horário em que o CI roda.

## Scope boundaries

- Escopo é só `activity_heatmap`/`_activity_years`. Outros lugares que usam
  `date.today()` (ex.: aging de defeitos em `defects_report`) comparam
  LOCAL-com-LOCAL de ponta a ponta — não têm o mesmo bug, verificado.
- Não muda a semântica de `opened`/`created` (continuam local); a correção é
  só no ponto de agregação do heatmap.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build+suíte verdes (159 testes); teste de regressão não depende de wall-clock.
- [x] Chore/bugfix; comportamento já documentado na spec `reporting` (#10), sem mudança de contrato.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
