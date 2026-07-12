# Change 0057-mapa-de-risco-get-risk-map-cruza-churn-de-git-su — Mapa de Risco: GET /risk-map cruza churn de git (subprocess, git log --name-only por arquivo, janela configuravel em dias) com defeitos (commits cuja mensagem referencia um DF-ID real do indice) e pass rate de automacao do repo (reaproveita metrics.automation_report), por repositorio configurado em arbites.yaml (risk_repos: name + local_path, mesma forma de automation_targets, lista separada pois o repo sob teste automatizado pode nao ser o mesmo do codigo fonte). Path invalido vira erro no payload (nunca derruba a rota). Visualizacao GitHub-heatmap-style no Dashboard: grade de quadrados por arquivo, intensidade de cor = churn, marcador vermelho = commit ligado a defeito.

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** risk-map

## Why

Mapa de Risco: GET /risk-map cruza churn de git (subprocess, git log --name-only por arquivo, janela configuravel em dias) com defeitos (commits cuja mensagem referencia um DF-ID real do indice) e pass rate de automacao do repo (reaproveita metrics.automation_report), por repositorio configurado em arbites.yaml (risk_repos: name + local_path, mesma forma de automation_targets, lista separada pois o repo sob teste automatizado pode nao ser o mesmo do codigo fonte). Path invalido vira erro no payload (nunca derruba a rota). Visualizacao GitHub-heatmap-style no Dashboard: grade de quadrados por arquivo, intensidade de cor = churn, marcador vermelho = commit ligado a defeito.

## What

Nova capability `risk-map`. Backend: `backend/arbites/risk_map.py`
(`scan_repo()`/`build()`, `git log` via subprocess read-only, cruzamento
com defeitos reais via regex `DF-\d+`, pass rate via
`metrics.automation_report`), config `risk_repos` no `DEFAULT_CONFIG`
(`workspace.py`), endpoint `GET /risk-map?days=` em `api.py`. Frontend:
`RiskMapPanel` no Dashboard (grade heatmap por arquivo, cores
`risk-heat-0..4` em `styles.css`), tipos em `types.ts`, client
`riskMap()` em `api.ts`.

## Scope boundaries

Não escreve no repositório do usuário — todo acesso via `git log` é
read-only. Não suporta outro VCS além de git. Não tenta correlacionar
arquivo↔squad/story além da menção de DF-ID no commit (não há esse vínculo
hoje no modelo de dados do Arbites).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
