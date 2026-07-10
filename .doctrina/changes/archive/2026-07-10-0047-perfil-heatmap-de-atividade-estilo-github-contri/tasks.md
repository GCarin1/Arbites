# Tasks — Change 0047

- [x] `metrics.activity_heatmap(conn, days=371)` — janela alinhada à segunda; agrega 5 fontes datadas.
- [x] `GET /metrics/activity?days=` no api.py.
- [x] Frontend: types `ActivityDay`/`ActivityHeatmapData` + `api.metricsActivity`.
- [x] `ActivityHeatmap.tsx` — grade Seg→Dom × semanas, rótulos de mês, seletor de métrica,
      tooltips por dia, legenda menos→mais; cores no verde do projeto (color-mix com --success).
- [x] CSS `.heatmap*` + `.heat-0..4`; renderizado na página de Perfil.
- [x] Testes backend (agregação diária, janela na segunda + ~53 semanas, vazio) + suíte verde (150) + build.
- [x] Smoke HTTP real (from numa segunda, buckets diários corretos).

## Closing steps

- [x] Apply: merge delta na spec reporting.
- [x] Archive.
- [x] Update index.json.
