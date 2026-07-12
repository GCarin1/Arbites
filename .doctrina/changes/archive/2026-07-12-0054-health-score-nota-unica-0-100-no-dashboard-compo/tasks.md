# Tasks — Change 0054

- [x] `metrics.health_score` — 4 componentes (coverage/defects/automation/debt), pesos
      configuráveis com renormalização, componente sem dado fica `None` (não conta como 0).
- [x] Bug corrigido no processo: `defects_pct` sempre tinha valor (0 defeitos = 100, mesmo
      em workspace vazio) — corrigido pra só pontuar quando há CT ou defeito no workspace.
- [x] `GET /metrics/health?sprint=&days=&squad=` lendo `health_score.weights` do arbites.yaml.
- [x] Frontend: `HealthScore`/`HealthComponent` types; `api.metricsHealth`; `HealthScoreCard`
      em destaque no topo do Dashboard (nota grande + 4 componentes com tooltip da fórmula).
- [x] CSS `.health-score-*` com semáforo (ok/warn/bad) reusando as cores já usadas em métricas.
- [x] Testes (workspace vazio, fórmulas explícitas, penalidade por severidade, pesos customizados,
      componente automação via runs de CI, dataset completo com os 4 componentes) + suíte
      verde (171) + build.
- [x] Smoke HTTP real (vazio → null; com CT+defeito → score calculado).

## Closing steps

- [x] Apply: merge delta na spec reporting.
- [x] Archive.
- [x] Update index.json.
