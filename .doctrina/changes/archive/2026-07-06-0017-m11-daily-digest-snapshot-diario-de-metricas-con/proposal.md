# Change 0017-m11-daily-digest-snapshot-diario-de-metricas-con — M11 daily digest: snapshot diario de metricas, contexto do dia (todos+atividade+diff+defeitos), geracao por IA (preview) com resumo/impedimentos/andamento/action items, salvar dailies/AAAA-MM-DD.md, listar por data, action items viram todos

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** daily

## Why

M11 daily digest: snapshot diario de metricas, contexto do dia (todos+atividade+diff+defeitos), geracao por IA (preview) com resumo/impedimentos/andamento/action items, salvar dailies/AAAA-MM-DD.md, listar por data, action items viram todos

## What

- **daily.py** (novo) — snapshot diário (`metrics/AAAA-MM-DD.json`), diff dia vs.
  anterior, atividade do dia (execuções movimentadas + defeitos abertos), contexto
  completo e render markdown para a IA/leitura.
- **ai.py** — schema `DailyDigest` + `generate_daily(provider, context_md)`.
- **api.py** — `POST /metrics/snapshot`, `GET /daily/{date}/context`,
  `POST /daily/{date}/generate` (preview, requer provider), `GET /dailies`,
  `GET/PUT /daily/{date}`.
- **workspace.py** — subdirs `dailies/` e `metrics/`.
- **Frontend** — página Daily (`Daily.tsx`): calendário (date picker), snapshot,
  gerar com IA, texto editável, tabela de diff de métricas, contexto do dia, e
  action items → afazeres; histórico de dailies salvas.
- **Testes** — `backend/tests/test_daily.py` (snapshot/diff, contexto, geração
  preview, salvar/listar + action item→todo, contexto sem IA).

## Scope boundaries

- IA é opcional (reusa provider do M5); sem provider a página serve o contexto
  para escrita manual. Geração é sempre preview; nada grava sem aceite.
- Reuniões e sua ingestão são M12 (Optional na spec).
- Calendário é date picker nativo; grade mensal fica no Future.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 86 + build do frontend).
- [x] Os 4 critérios de `daily` verificados por `backend/tests/test_daily.py` (`doctrina coverage`).
- [x] IA opcional: `test_daily_context_without_ai_still_works` cobre o caminho sem chamar provider.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
