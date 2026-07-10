# Change 0039-bugs-do-modal-de-execucao-1-botao-fechar-duplica — bugs do modal de execucao: (1) botao Fechar duplicado no footer alem do X do header — manter so o X (footer do Modal vira opcional); (2) salvar comentario sem feedback e efeito de reset preso a result.comment — dar feedback (Salvar/Salvando/Salvo, desabilita quando sem mudanca) e resetar so ao trocar de CT

- **Status:** applied
- **Applied:** 2026-07-10
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** (none — chore)

## Why

bugs do modal de execucao: (1) botao Fechar duplicado no footer alem do X do header — manter so o X (footer do Modal vira opcional); (2) salvar comentario sem feedback e efeito de reset preso a result.comment — dar feedback (Salvar/Salvando/Salvo, desabilita quando sem mudanca) e resetar so ao trocar de CT

## What

- **frontend/src/components/Modal.tsx** — `footer` vira opcional; sem footer o
  único fechar é o X do header (elimina o botão "Fechar" duplicado).
- **frontend/src/components/Executions.tsx** — o `Modal` do `ResultPanel` deixa
  de passar `footer`. Comentário: feedback de salvamento (dirty/saving/saved) e
  o efeito de reset passa a depender só do id do CT (não de `result.comment`),
  para um refresh de fundo não reescrever o que o usuário está digitando;
  `saveComment` preserva a coluna atual.

## Bugs corrigidos (skills)

- Botão de fechar duplicado (X + "Fechar") → `modal-fechar-duplicado-x-e-footer`.
- Salvar sem feedback / reset preso a valor do servidor →
  `salvar-manual-feedback-e-reset-por-id`.

## Scope boundaries

- Chore UI; sem alteração de backend/endpoint. O save de comentário já
  funcionava na API (verificado); aqui é robustez/feedback no frontend.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build frontend verde (`tsc --noEmit`); API de salvar comentário verificada com servidor real.
- [x] Chore UI-only; sem critérios de spec.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
