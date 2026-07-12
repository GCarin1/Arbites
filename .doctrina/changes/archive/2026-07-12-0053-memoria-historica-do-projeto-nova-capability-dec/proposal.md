# Change 0053-memoria-historica-do-projeto-nova-capability-dec — Memoria Historica do Projeto: nova capability decisions. Decisoes arquiteturais do TIME DE QA sobre o projeto sob teste (nao o sistema de ADR do proprio Doctrina) — ponteiro + metadados como defects: titulo, status (proposed/accepted/superseded), squad, tags, supersedes, corpo com template Contexto/Decisao/Consequencias. CRUD completo GET/POST/PUT/DELETE, filtro por status/squad, pesquisavel via /search (kind=decision) e mencionavel @DEC-XXXX em qualquer texto (Todos, comentarios de execucao, etc). Nova aba Decisoes na navegacao com navegacao por mencao

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** decisions (nova) decisions

## Why

Memoria Historica do Projeto: nova capability decisions. Decisoes arquiteturais do TIME DE QA sobre o projeto sob teste (nao o sistema de ADR do proprio Doctrina) — ponteiro + metadados como defects: titulo, status (proposed/accepted/superseded), squad, tags, supersedes, corpo com template Contexto/Decisao/Consequencias. CRUD completo GET/POST/PUT/DELETE, filtro por status/squad, pesquisavel via /search (kind=decision) e mencionavel @DEC-XXXX em qualquer texto (Todos, comentarios de execucao, etc). Nova aba Decisoes na navegacao com navegacao por mencao

## What

Segunda das 6 ideias do "documento de memória de projeto/IA": decisões
arquiteturais do time de QA sobre o projeto sob teste, mirror do padrão de
`defects` (ponteiro + metadados).

- **backend/arbites/workspace.py** — `decisions/` em `SUBDIRS`;
  `id_prefixes` ganha `decision: DEC` (merge sobre default, sem migração
  manual para workspaces existentes).
- **backend/arbites/indexer.py** — tabela `decisions`; `_insert_decision`;
  integrado em `reindex_full`/`reindex_file`/`_find_id` (mesma disciplina
  de detecção de ID duplicado das outras capabilities).
- **backend/arbites/api.py** — CRUD completo (`GET/POST /decisions`,
  `GET/PUT/DELETE /decisions/{id}`); `DEFAULT_DECISION_BODY` (template
  Contexto/Decisão/Consequências); `decision` vira `kind` pesquisável em
  `GET /search` e resolvível em `_resolve_link` (um Afazer pode linkar pra
  uma decisão, mesmo mecanismo já usado para CT/execução/defeito).
- **frontend** — `Decision` type, `api.ts`, `Decisions.tsx` (lista estilo
  cards — mesmo padrão visual de Afazeres — com filtro de status e modal
  com os 3 campos do corpo via `MentionTextarea` + `supersedes` via
  `SingleRefInput`); nova aba "Decisões"; `navigateTo` ganha `DEC-XXXX`.
- **`.doctrina/specs/decisions/spec.md`** (nova, via `doctrina spec new`).

## Bug corrigido no processo

`DecisionIn.body` tinha default `str = ""` — o guard `payload.body is not
None else DEFAULT_DECISION_BODY` nunca ativava o template (string vazia
passa no `is not None`). Corrigido para `str | None = None`, o mesmo padrão
já usado em `TestcaseIn.body` (que EXISTE precisamente por essa razão).

## Scope boundaries

- **Não** toca `.doctrina/decisions/` (ADRs do próprio Doctrina) — namespace
  e propósito totalmente separados, confirmado com o usuário antes de
  implementar.
- Não é um chat/interface conversacional sobre a memória histórica — é
  browsable/buscável/mencionável. Uma interface de "conversa" fica anotada
  como aspiracional; o consumo por agentes externos é a capability separada
  de Context Pack.
- `supersedes` é um campo livre (id de outra decisão), sem validação de
  existência no momento da gravação — mesma filosofia leve de `testcase`/
  `execution` em `defects`.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (165 testes backend + build frontend).
- [x] Critérios #1-#3 do decisions citam `backend/tests/test_decisions.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
