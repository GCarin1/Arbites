# Tasks — Change 0051 (chore / bugfix)

- [x] Diagnóstico: reproduzido com servidor real ("EXEC" via API + exec_ops direto), confirmado o
      corte de dados em `result_events`/`executions.created_at` (UTC) vs `date.today()` (local).
- [x] `metrics._local_date(iso)`: converte timestamp UTC-aware para data local; identidade p/ data local pura.
- [x] `activity_heatmap`: `result_events.at`/`executions.created_at` (auto_runs) passam por `_local_date`
      linha a linha; as 3 fontes já-locais (defects/testcases/requirements) seguem via SQL GROUP BY.
- [x] `_activity_years`: mesmo fix (virada de ano UTC × local).
- [x] Removido `_ACTIVITY_DATE_EXPRS` (tupla morta, nunca referenciada).
- [x] Teste de regressão determinístico (`test_local_date_converts_utc_iso_consistently_with_python`)
      + suíte de heatmap volta a passar de forma estável (antes falhava dependendo da hora do dia) + build.

## Closing steps

- [x] Apply (chore, zero deltas).
- [x] Archive.
- [x] Update index.json.
