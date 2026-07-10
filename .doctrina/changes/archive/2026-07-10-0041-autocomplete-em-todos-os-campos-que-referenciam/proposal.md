# Change 0041-autocomplete-em-todos-os-campos-que-referenciam — autocomplete em todos os campos que referenciam um item existente, reutilizando GET /search: novo SingleRefInput (referencia unica por id/titulo) substitui o select de vincular defeito e o campo cru de story do CT; comentario do resultado vira MentionTextarea (@ referencia um card); rende links clicaveis ja existentes

- **Status:** applied
- **Applied:** 2026-07-10
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** (none — chore)

## Why

autocomplete em todos os campos que referenciam um item existente, reutilizando GET /search: novo SingleRefInput (referencia unica por id/titulo) substitui o select de vincular defeito e o campo cru de story do CT; comentario do resultado vira MentionTextarea (@ referencia um card); rende links clicaveis ja existentes

## What

Reutiliza o endpoint `GET /search` (já existente, spec `todos`) para levar
autocomplete a todo campo que referencia um item existente.

- **frontend/src/components/Autocomplete.tsx** — `useSuggestions(query, kinds)`
  agora filtra por tipo; novo `SingleRefInput` (caixa de texto que sugere e
  grava UM id) substitui `<select>`/campo de id cru.
- **frontend/src/components/Executions.tsx** — "vincular defeito existente" vira
  `SingleRefInput` (kinds=defect), digitável (não mais `<select>`); o comentário
  do resultado vira `MentionTextarea` (digite `@` para referenciar um card),
  read-only quando a execução está fechada.
- **frontend/src/components/TestCaseEditor.tsx** — campo Story vira
  `SingleRefInput` (kinds=requirement).
- Menções `@ID` já renderizam como links clicáveis (`mention-link`, ReadView).

## Comportamento documentado (skill)

- `campos-de-referencia-com-autocomplete`: todo campo que referencia um item
  (id único, lista de links, descrição/comentário com `@`) usa o mesmo
  autocomplete via `/search`; o item vinculado é visível/clicável.

## Scope boundaries

- Chore UI: reusa `/search` (sem endpoint novo). Não reescreve os campos de
  Requirements/Defect-create ainda; cobre os pontos pedidos (defeito, story,
  comentário). Extensível aos demais com o mesmo `SingleRefInput`.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build frontend verde; `/search?kinds=` verificado com servidor real.
- [x] Chore UI-only; reusa capability já speced (todos: `/search`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
