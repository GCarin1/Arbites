# Tasks — Change 0057-mapa-de-risco-get-risk-map-cruza-churn-de-git-su

- [x] Config `risk_repos: []` no `DEFAULT_CONFIG` (`workspace.py`).
- [x] `backend/arbites/risk_map.py`: `_git_log` (subprocess read-only),
      `scan_repo` (churn + defect_commits + pass rate), `build`.
- [x] Endpoint `GET /risk-map?days=` em `api.py`.
- [x] Testes `backend/tests/test_risk_map.py` (8 casos, com repo git real
      criado via subprocess no tmp_path) + suíte completa (201/201) verde.
- [x] Frontend: `RiskMapPanel`/`riskLevel()` em `Dashboard.tsx`, tipos em
      `types.ts`, client `riskMap()` em `api.ts`, CSS `.risk-heat-0..4`/
      `.risk-map-grid`/`.risk-map-cell` em `styles.css`.
- [x] `npm run build` limpo (typecheck + vite build).
- [x] Smoke test contra servidor real: repo git real com 3 commits (1
      referenciando um DF-ID real) → `a.py` churn=3 defect_commits=1,
      `b.py` churn=1 defect_commits=0.
- [x] Spec `risk-map` escrita (`doctrina spec new risk-map` + conteúdo
      completo).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-12-0057-mapa-de-risco-get-risk-map-cruza-churn-de-git-su/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
