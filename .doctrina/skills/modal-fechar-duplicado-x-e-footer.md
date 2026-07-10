---
name: modal-fechar-duplicado-x-e-footer
description: Um componente Modal com X no header E um footer sempre-presente com botão "Fechar" mostra dois controles de fechar redundantes. Torne o footer opcional e, para modais só de leitura/edição-inline, feche só pelo X.
when: Ao abrir um Modal cujo conteúdo já se auto-salva ou não tem ação de confirmar/cancelar, e o footer só teria um botão "Fechar" — resultando em X (header) + Fechar (footer) duplicados.
---

# Skill — modal-fechar-duplicado-x-e-footer

## When to use this skill

- Vai reusar um `<Modal>` para um conteúdo SEM ação de confirmar (editor que
  salva sozinho/por botão próprio, painel de leitura). O footer só teria um
  "Fechar".
- Sintoma: o usuário reclama de dois botões de fechar (o `×` do cabeçalho e um
  "Fechar" embaixo).

## Procedure

1. Torne `footer` **opcional** no `Modal` (`footer?: ReactNode`) e só renderize
   `.modal-footer` quando houver footer: `{footer && <div className="modal-footer">…</div>}`.
2. Para modais sem confirmação, **não passe footer** — o `×` do header (+ Esc +
   backdrop) já fecha. Reserve o footer para modais com Cancelar/Confirmar.

## Anti-patterns

- Deixar o footer obrigatório e preencher com um "Fechar" que duplica o X.
- Ter dois caminhos visuais de fechar quando um só (o X) basta.

## Related material

- `frontend/src/components/Modal.tsx` — `footer?` opcional.
- `frontend/src/components/Executions.tsx` — modal do `ResultPanel` (só X).
