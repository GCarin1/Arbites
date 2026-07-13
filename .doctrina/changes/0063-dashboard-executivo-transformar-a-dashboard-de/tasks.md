# Tasks — Change 0063-dashboard-executivo-transformar-a-dashboard-de

- [ ] Backend: comparação com período anterior no summary
      (`previous`/`delta` por métrica, janelas consecutivas de mesmo
      tamanho) + testes.
- [ ] Backend: endpoint/agregado de alertas de risco reutilizando
      `audit.collect_findings` (achados bad) + Health Score em queda.
- [ ] Backend: agregado "top problemas" (piores repos, CTs que mais falham,
      defeitos mais antigos — dados que os reports já têm).
- [ ] Backend: "ações recomendadas" por regra determinística + testes.
- [ ] Frontend: bloco de alertas no topo (clicáveis), deltas nos KPI cards
      (↑↓ vs período anterior), seções top problemas / ações recomendadas,
      caption "dados de HH:MM" via `last_reindex`.
- [ ] Suíte completa verde + `npm run build` limpo + smoke test em servidor
      real.
- [ ] Atualizar spec reporting: critérios #13/#14 → verified; bump minor.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0063-dashboard-executivo-transformar-a-dashboard-de/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
