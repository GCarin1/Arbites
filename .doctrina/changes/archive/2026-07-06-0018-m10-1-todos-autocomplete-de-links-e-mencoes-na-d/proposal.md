# Change 0018-m10-1-todos-autocomplete-de-links-e-mencoes-na-d — M10.1 todos: autocomplete de links e mencoes @ na descricao (endpoint de busca de entidades), export de todos em markdown e xml, filtro por data, selecao multipla com exclusao em massa e descricao expansivel

- **Status:** proposed
- **Date:** 2026-07-06
- **Owner:**
- **Affects specs:** todos

## Why

M10.1 todos: autocomplete de links e mencoes @ na descricao (endpoint de busca de entidades), export de todos em markdown e xml, filtro por data, selecao multipla com exclusao em massa e descricao expansivel

## What

- **api.py** — `GET /search` (autocomplete cross-entidade por id/título, filtrável por kind);
  `GET /todos/export?format=md|xml` (respeita filtros ou `ids` selecionados, inclui a descrição);
  helpers `_todos_markdown`/`_todos_xml` (XML escapado).
- **Frontend** — `Autocomplete.tsx` (novo): `LinksInput` (autocomplete por token no campo de
  links) e `MentionTextarea` (menções `@` na descrição, navegáveis por teclado/mouse). Aba
  **Afazeres** reescrita: filtro por período de prazo, export MD/XML, seleção múltipla com
  barra de ações + exclusão em massa (modal "irá excluir X itens"), botão Editar desabilitado
  com >1 selecionado, e descrição expansível por linha.
- **Testes** — `test_search_entities_for_autocomplete` e `test_export_todos_md_and_xml`.

## Scope boundaries

- Autocomplete/menções e seleção são UI; o backend só provê busca e export (testados).
- Menção `@` insere o id do documento no texto (referência textual); não cria vínculo estruturado.
- Reuniões (M12) seguem fora deste escopo.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 88 + build do frontend).
- [x] Critérios todos#5 (search) e todos#6 (export) verificados por `backend/tests/test_todos.py` (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
