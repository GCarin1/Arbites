# Spec Delta — capability: reporting

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/reporting/spec.md`

---

## Context

M8 promove o item "metas/thresholds configuráveis por métrica" de *Future*
para committed. Metas ficam em `arbites.yaml` (`metric_thresholds`); o
`/metrics/summary` anota cada métrica com `status` (ok/warn/bad) e a
`threshold` usada, respeitando a direção (maior-melhor para pass_rate e
coberturas; menor-melhor para blocked_rate/rework_rate). O dashboard colore
os KPI cards como semáforo. Sem metas configuradas → `status: none`
(retrocompatível).

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall anotar cada métrica do summary com um `status`
  (ok/warn/bad/none) contra metas opcionais configuradas em
  `arbites.yaml` (`metric_thresholds`), respeitando a direção da métrica
  (maior-melhor ou menor-melhor).

### State-driven (ADDED)

- While nenhuma meta está configurada para uma métrica, the system shall
  reportar `status: none` e não colorir o card (o número e a fórmula seguem
  visíveis).

## Acceptance criteria (ADDED)

6. [verified] Cada métrica recebe status ok/warn/bad conforme a meta e a
   direção configuradas, e `none` quando não há meta — verified by
   `backend/tests/test_metrics.py`.

## Maturity (MODIFIED)

Remover de **Future** o item "metas/thresholds configuráveis por métrica"
(agora committed). Permanece em Future apenas "Comparação entre sprints".
