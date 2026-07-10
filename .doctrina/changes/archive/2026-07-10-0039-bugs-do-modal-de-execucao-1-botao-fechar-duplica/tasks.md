# Tasks — Change 0039 (chore)

- [x] `Modal`: `footer` opcional; não renderiza `.modal-footer` quando ausente.
- [x] `ResultPanel` no `Modal` sem footer → só o X fecha (remove "Fechar" duplicado).
- [x] Salvar comentário: estado `savingComment` + `commentDirty`; botão "Salvar comentário"/"Salvando…"/"Salvo", desabilitado quando sem mudança.
- [x] Efeito de reset do comentário passa a depender só de `result.testcase_id` (não `result.comment`), para refresh de fundo não sobrescrever o texto em edição.
- [x] `saveComment` preserva a coluna atual (`column: result.column || result.status`).
- [x] Build frontend verde; save-comment verificado por API real (persiste).

## Closing steps

- [x] Apply (chore, zero deltas).
- [x] Archive the change folder.
- [x] Update `.doctrina/index.json`.
