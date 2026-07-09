# Change 0029-requisitos-e-execucoes-replicam-o-layout-de-repo — requisitos e execucoes replicam o layout de repositorio: hierarquia centralizada no conteudo (epic-story com drag-and-drop de story entre epics; execucoes agrupadas por ano), detalhe por clique com botao Voltar, exclusao com confirmacao e data de criacao registrada/exibida

- **Status:** proposed
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** requirements

## Why

requisitos e execucoes replicam o layout de repositorio: hierarquia centralizada no conteudo (epic-story com drag-and-drop de story entre epics; execucoes agrupadas por ano), detalhe por clique com botao Voltar, exclusao com confirmacao e data de criacao registrada/exibida

## What

- **Requisitos** — novo `ReqRepository` (centralizado no conteúdo): hierarquia
  epic→story com expandir/colapsar, **drag & drop de story para outro epic**
  (reassocia via PUT `epic`; soltar em "sem epic/" desassocia), exclusão com
  confirmação, `created` carimbado/indexado/exibido; detalhe abre por clique
  com "← Voltar".
- **Execuções** — novo `ExecutionsRepo` (centralizado): agrupado por **ano de
  criação** (a pasta natural da execution) com expandir/colapsar, contadores
  passed/total, status e data; board abre por clique com "← Voltar"; criação
  também com Voltar.
- **App.tsx** — sidebar dos dois vira hint; listas saem do painel lateral.
- **indexer/api** — coluna `created` em requirements + carimbo na criação.
- **Teste** — `test_requirement_created_stamped_and_indexed`.

## Scope boundaries

- Execuções NÃO têm drag & drop nem exclusão: o histórico de execução é
  imutável por design (ADR 0005) e o diretório é derivado do ano de criação —
  desvio deliberado do doc §1.3, registrado aqui.
- Drag & drop de requisito é semântico (story↔epic), não pasta física — a
  hierarquia de requisitos é epic→story, não filesystem.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build + pytest 106 verdes.
- [x] requirements 4/4 no coverage (`created` testado).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
