# Change 0044-aba-defeitos-pagina-dedicada-de-gerenciamento-de — aba Defeitos: pagina dedicada de gerenciamento de bugs (antes so dava pra criar um defeito a partir de um resultado failed numa execucao, sem lista/edicao/exclusao proprias). Nova aba na navegacao com filtro por status/severidade, criacao avulsa (vincular CT/execucao opcional via autocomplete), edicao, mudanca rapida de status, exclusao, e navegacao @DF-XXXX abre direto no editor. Backend ganha GET /defects/{id} (com corpo) e DELETE /defects/{id}

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** defects

## Why

aba Defeitos: pagina dedicada de gerenciamento de bugs (antes so dava pra criar um defeito a partir de um resultado failed numa execucao, sem lista/edicao/exclusao proprias). Nova aba na navegacao com filtro por status/severidade, criacao avulsa (vincular CT/execucao opcional via autocomplete), edicao, mudanca rapida de status, exclusao, e navegacao @DF-XXXX abre direto no editor. Backend ganha GET /defects/{id} (com corpo) e DELETE /defects/{id}

## What

O usuário notou que faltava um lugar pra gerenciar defeitos — só dava pra
criar um a partir de um resultado `failed` numa execução (`NewDefectModal`),
sem lista, edição avulsa ou exclusão próprias.

- **backend/arbites/api.py** — `GET /defects/{id}` (expõe `_defect_out`, que
  já existia internamente mas não tinha rota própria — inclui o corpo, que
  a listagem `GET /defects` não traz); `DELETE /defects/{id}` (mesmo padrão
  de `delete_todo`: `ws.trash()` + reindex).
- **frontend/src/components/Defects.tsx** (novo) — página com tabela
  (filtro por status/severidade, coluna de "aberto há N dias"), botão "Novo
  defeito" e "Editar" abrindo um `Modal` com `SingleRefInput` (CT/execução,
  ambos opcionais) e `MentionTextarea` (descrição com `@menções`); mudança
  rápida de status via `<select>` inline na linha; exclusão com confirmação.
- **frontend/src/App.tsx** — nova aba "Defeitos" (grupo Acompanhamento);
  `navigateTo` ganha o ramo `DF-XXXX` (antes explicitamente comentado como
  "sem view dedicada — sem navegação"); `selectedDefect`/`openId`/`onOpened`
  abrem o editor direto quando se chega via uma menção `@DF-XXXX`.
- **defects spec** MODIFIED (delta) + critério [verified] #5.

## Reuso deliberado

- Cor de severidade: reusei o `SEV_DOT` já existente em `Dashboard.tsx`
  (`DefectsPanel`) em vez de inventar um esquema novo.
- Vínculo a CT/execução: `SingleRefInput` (autocomplete via `/search`),
  mesmo padrão já estabelecido para "vincular defeito existente" no modal
  de resultado de execução (change 0041).

## Scope boundaries

- Continua "ponteiro + metadados", não um bug tracker completo (sem
  workflow de triagem/atribuição/comentários — princípio já explícito na
  spec `defects`).
- Não adiciona busca textual nem paginação na listagem (dataset esperado é
  pequeno; filtro client-side de severidade é suficiente por ora).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (138 testes backend + build frontend).
- [x] Critério #5 do defects cita `backend/tests/test_defects.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
