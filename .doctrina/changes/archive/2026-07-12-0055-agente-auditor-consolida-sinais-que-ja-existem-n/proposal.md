# Change 0055-agente-auditor-consolida-sinais-que-ja-existem-n — Agente Auditor: consolida sinais que ja existem no indice (warnings de indexacao, stories sem CT, defeitos abertos ha muito tempo sem causa raiz, automacoes quebradas ha varios dias) num snapshot datado, persistido como Markdown em audits/ (AUD-NNNN). Sem daemon: POST /audit/run roda sob demanda; GET /audit/latest reaproveita a ultima rodada se ainda estiver fresca (menos de audit.auto_interval_hours, default 24h) ou dispara uma nova (trigger=auto) se estiver velha/inexistente. GET /audit/history lista rodadas passadas; GET /audit/{id} devolve o detalhe. Cada achado tem categoria/codigo/severidade(bad|warn|info)/mensagem/ref, ordenados pior-primeiro. Limiares (defect_aging_days default 14, broken_automation_days default 3) configuraveis em arbites.yaml (audit.*).

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** audit

## Why

Agente Auditor: consolida sinais que ja existem no indice (warnings de indexacao, stories sem CT, defeitos abertos ha muito tempo sem causa raiz, automacoes quebradas ha varios dias) num snapshot datado, persistido como Markdown em audits/ (AUD-NNNN). Sem daemon: POST /audit/run roda sob demanda; GET /audit/latest reaproveita a ultima rodada se ainda estiver fresca (menos de audit.auto_interval_hours, default 24h) ou dispara uma nova (trigger=auto) se estiver velha/inexistente. GET /audit/history lista rodadas passadas; GET /audit/{id} devolve o detalhe. Cada achado tem categoria/codigo/severidade(bad|warn|info)/mensagem/ref, ordenados pior-primeiro. Limiares (defect_aging_days default 14, broken_automation_days default 3) configuraveis em arbites.yaml (audit.*).

## What

Nova capability `audit` (Agente Auditor). Backend: `backend/arbites/audit.py`
(`collect_findings`/`summarize`/`audit_markdown`), tabela `audits` no
indexer, SUBDIR `audits/` e prefixo de ID `AUD` no workspace, endpoints
`POST /audit/run`, `GET /audit/latest`, `GET /audit/history`,
`GET /audit/{id}` em `api.py`. Frontend: `frontend/src/components/Audit.tsx`
(botão "Auditar agora", resumo por severidade, achados agrupados por
categoria, histórico clicável), tipos e client em `types.ts`/`api.ts`, nova
aba "Auditoria" no menu (`App.tsx`).

## Scope boundaries

Não implementa um scheduler/daemon real — a auto-execução é lazy, disparada
por `GET /audit/latest` quando a última rodada está velha, não por um cron
em background (Arbites é local-first, não "sempre ligado"). Não adiciona
novos tipos de check além dos 4 especificados na spec — reaproveita dados
que já existiam no índice (warnings, defeitos, automação), sem heurística
nova.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
