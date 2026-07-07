# Change 0022-m12-meetings-capability-de-reunioes-crud-em-meet — M12 meetings: capability de reunioes — CRUD em meetings/*.md (tema, data, corpo), resumo executivo por IA (preview), inclusao das reunioes do dia no contexto da daily; frontend aba Reunioes

- **Status:** proposed
- **Date:** 2026-07-07
- **Owner:**
- **Affects specs:** meetings

## Why

M12 meetings: capability de reunioes — CRUD em meetings/*.md (tema, data, corpo), resumo executivo por IA (preview), inclusao das reunioes do dia no contexto da daily; frontend aba Reunioes

## What

- **workspace.py** — prefixo `meeting` (`MTG-`) e subdir `meetings/`.
- **indexer.py** — tabela `meetings` (id/title/date/summary); insert + reindex
  completo/incremental + `_find_id`.
- **ai.py** — schema `MeetingSummary` + `summarize_meeting(provider, body)`.
- **api.py** — CRUD `GET/POST/PUT/DELETE /meetings` (filtro por data),
  `POST /meetings/{id}/summarize` (preview, requer provider); `meeting` incluído no `/search`.
- **daily.py** — contexto do dia passa a incluir as reuniões daquele dia
  (`_meetings_of_day`) e o markdown ganha a seção "Reuniões do dia".
- **Frontend** — aba **Reuniões** (`Meetings.tsx`): lista por data, linhas
  expansíveis (resumo + descrição), e modal com tema/data/descrição, "Resumir
  com IA" (preview → resumo editável) e salvar.
- **Testes** — `backend/tests/test_meetings.py` (CRUD/filtro, summarize preview→save,
  corpo vazio 422, reuniões no contexto da daily).

## Scope boundaries

- IA opcional (reusa provider do M5); registro/leitura funcionam sem provider.
- Sem gravação/transcrição de áudio (o usuário cola a descrição/transcrição).
- Extração de action items da reunião → afazeres fica no Future da spec.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 92 + build do frontend).
- [x] Os 3 critérios de `meetings` verificados por `backend/tests/test_meetings.py` (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
