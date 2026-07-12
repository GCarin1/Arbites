# Spec Delta — capability: risk-map

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/risk-map/spec.md`

Note: o conteúdo completo já foi escrito diretamente em
`.doctrina/specs/risk-map/spec.md` via `doctrina spec new risk-map` +
edição manual (mesmo padrão usado nas changes 0053/0055/0056, capabilities
`decisions`/`audit`/`context-pack`) — este delta documenta o que entrou,
`Operation: MODIFIED` porque o arquivo alvo já existe (criado pelo
scaffold) em vez de `ADDED`.

---

Nova capability `risk-map` (Mapa de Risco):

- `GET /risk-map?days=` (default 90) escaneia cada repo em `risk_repos`
  (`arbites.yaml`) via `git log` local, read-only.
- Por arquivo: `churn` (nº commits) e `defect_commits` (nº commits cuja
  mensagem referencia um `DF-\d+` que existe de fato no índice).
- Por repo: pass rate de automação (casado pelo nome com
  `metrics.automation_report`), total de commits, arquivos ordenados por
  churn (pior-primeiro, top N).
- `local_path` inválido/ausente vira `error` no payload daquele repo, sem
  derrubar a rota nem os demais repos configurados.
- Frontend: heatmap estilo GitHub no Dashboard (grade de quadrados,
  intensidade de cor = churn, marcador vermelho = commit ligado a defeito).

5 critérios de aceitação, todos `[verified]` — ver
`backend/tests/test_risk_map.py` (8 testes).
