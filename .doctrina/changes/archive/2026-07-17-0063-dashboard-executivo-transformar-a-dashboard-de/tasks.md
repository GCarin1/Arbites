# Tasks — Change 0063-dashboard-executivo-transformar-a-dashboard-de

- [x] Backend: `metrics.period_pass_rate` (janela atual vs anterior via
      `_results_where` estendido com `until`) — variação de pass rate.
- [x] Backend: `metrics.top_problems` (piores repos + CTs que mais falham +
      defeitos mais antigos, ordenados) reaproveitando os reports existentes.
- [x] Backend: endpoint `GET /metrics/dashboard` que assembla
      pass_rate_trend + alertas (achados `bad` do Auditor + Health Score
      baixo) + ações recomendadas (achados reformulados) + top_problems +
      last_reindex. Nada de coleta nova.
- [x] Backend: `backend/tests/test_dashboard_executive.py` (7 testes);
      suítes metrics/health/audit/automation verdes (43/43).
- [x] Frontend: `ExecutivePanel` no topo do Dashboard (alertas clicáveis,
      ações recomendadas, top problemas, caption "dados de HH:MM"); delta
      ▲▼ pts no KPI card de Pass rate; `metricsDashboard` no client/tipos;
      `onNavigate` do App para os alertas.
- [x] CSS `.exec-*`/`.metric-delta` no styles.css.
- [x] `npm run build` limpo.
- [x] Smoke real contra servidor: alerta de Health Score baixo, ação
      recomendada da story sem CT, defeito mais antigo em top_problems,
      `last_reindex` presente — tudo no payload real de
      `GET /metrics/dashboard`. Suíte completa 232/232.
- [x] Spec reporting: EARS `/metrics/dashboard` + critério #13; versão
      0.10.1 → 0.11.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-17-0063-dashboard-executivo-transformar-a-dashboard-de/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
