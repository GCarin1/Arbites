# Change 0059-fix-varredura-de-inconsistencias-entre — fix: varredura de inconsistencias entre capabilities novas e infra existente. (1) health_score, audit e risk_map chamavam automation_report sem o ci_monitoring.name_pattern configurado - com padrao customizado o componente de automacao do Health Score vira null, o auditor nunca acha automacao quebrada e o risk map perde o pass rate, tudo silencioso; (2) Memoria do Projeto: desmarcar todos os filtros de tipo mostrava TUDO em vez de nada (lista vazia virava param vazio = sem filtro); (3) prefixo de defeito DF- hardcoded no risk_map apesar de id_prefixes.defect ser configuravel; (4) falha ao gravar o log de agente derrubava a resposta da IA ja gerada; (5) TypeError nao capturado no audit com created_at naive editado externamente; (6) automation_report recomputado por repo no risk_map.build

- **Status:** applied
- **Applied:** 2026-07-13
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** reporting, audit, risk-map, project-memory

## Why

fix: varredura de inconsistencias entre capabilities novas e infra existente. (1) health_score, audit e risk_map chamavam automation_report sem o ci_monitoring.name_pattern configurado - com padrao customizado o componente de automacao do Health Score vira null, o auditor nunca acha automacao quebrada e o risk map perde o pass rate, tudo silencioso; (2) Memoria do Projeto: desmarcar todos os filtros de tipo mostrava TUDO em vez de nada (lista vazia virava param vazio = sem filtro); (3) prefixo de defeito DF- hardcoded no risk_map apesar de id_prefixes.defect ser configuravel; (4) falha ao gravar o log de agente derrubava a resposta da IA ja gerada; (5) TypeError nao capturado no audit com created_at naive editado externamente; (6) automation_report recomputado por repo no risk_map.build

## What

Backend: `metrics.health_score`, `audit.collect_findings`/`_broken_automations`
e `risk_map.scan_repo`/`build` ganham o parâmetro `name_pattern`, repassado
pelos endpoints em `api.py` (que leem `ci_monitoring.name_pattern` — mesmo
padrão que `/metrics/automation` já usava); `risk_map` ganha `defect_prefix`
(de `id_prefixes.defect`) e a regex `_DF_RE` hardcoded foi substituída por
`_defect_re(prefix)`; `build()` computa `automation_report` uma única vez e
repassa `pass_rate_by_repo` aos scans; `_broken_automations` captura
`TypeError` além de `ValueError`; `_log_agent_event` virou não-fatal
(try/except `OSError`/`sqlite3.Error` → warning). Frontend: `Memory.tsx`
trata seleção vazia de tipos como "nada a mostrar" sem chamar a API.
5 testes de regressão novos (218/218 no total).

## Scope boundaries

Não muda o comportamento default de nenhum endpoint (sem config customizada,
tudo idêntico). Não toca o endpoint `/metrics/automation` (que já estava
correto — ele era a referência). Não adiciona config nova: reutiliza
`ci_monitoring.name_pattern` e `id_prefixes.defect` que já existiam.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
