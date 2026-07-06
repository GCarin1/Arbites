# Change 0014-m8-metas-thresholds-no-dashboard-metas-configura — M8 metas/thresholds no dashboard: metas configuraveis por metrica no arbites.yaml (metric_thresholds); o summary anota cada metrica com status ok/warn/bad conforme a meta e direcao (maior-melhor p/ pass_rate e coberturas, menor-melhor p/ blocked/rework); frontend colore os KPI cards como semaforo

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** reporting

## Why

M8 metas/thresholds no dashboard: metas configuraveis por metrica no arbites.yaml (metric_thresholds); o summary anota cada metrica com status ok/warn/bad conforme a meta e direcao (maior-melhor p/ pass_rate e coberturas, menor-melhor p/ blocked/rework); frontend colore os KPI cards como semaforo

## What

- **metrics.py** — `threshold_status(value, cfg)` e `annotate_thresholds(summary, thresholds)`:
  cada métrica ganha `status` (ok/warn/bad/none) e a `threshold` usada. Direção
  default por métrica (pass_rate/coberturas = maior-melhor; blocked_rate/rework_rate
  = menor-melhor), sobreponível por `direction` no config.
- **api.py** — `/metrics/summary` lê `metric_thresholds` do `arbites.yaml` e anota o summary.
- **Frontend** — `MetricCard` colore o KPI como semáforo (borda + ponto) e mostra a meta
  na linha da fórmula; sem meta → sem cor (retrocompat).
- **Testes** — `test_metric_thresholds_traffic_light` e `test_thresholds_absent_by_default`.

## Scope boundaries

- Metas vivem no `arbites.yaml` (`metric_thresholds`), não numa entidade rica.
- Não altera as fórmulas das métricas — só anota status vs meta.
- "Comparação entre sprints" segue em Future; painel de defeitos é M9.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 75 + build do frontend).
- [x] Critério SC6 de `reporting` coberto por `backend/tests/test_metrics.py` (`doctrina coverage`).
- [x] Sem metas → `status: none` (retrocompat), verificado em `test_thresholds_absent_by_default`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
