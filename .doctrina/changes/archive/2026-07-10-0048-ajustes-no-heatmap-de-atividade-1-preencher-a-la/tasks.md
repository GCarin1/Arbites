# Tasks — Change 0048

- [x] Backend: `activity_heatmap(..., year=None)` (janela do ano civil) + `_activity_years` + `years` na resposta.
- [x] `GET /metrics/activity?year=` no api.py.
- [x] Frontend CSS: grade preenche o card (flex:1 nas colunas, células `aspect-ratio:1` — escalam com o card).
- [x] Frontend: seletor de ano; tooltip flutuante no cursor (`position:fixed` + clientX/clientY) com nº de mudanças + breakdown.
- [x] Testes backend (years list, year filter windowing) + suíte verde (152) + build.
- [x] Smoke HTTP real (default vs year=2026 vs year=2025).

## Closing steps

- [x] Apply: merge delta na spec reporting.
- [x] Archive.
- [x] Update index.json.
