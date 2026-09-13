# Change 0083-acoes-em-lote-no-repositorio-de-cts-e-nas — acoes em lote no repositorio de CTs e nas executions

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** testcases

## Why

Não há multi-seleção em lugar nenhum: mudar status de N CTs, mover N
CTs de pasta ou excluir N executions é um a um. Numa base migrada do Xray
(centenas de CTs) isso é dor real.

## What

- Repositório de CTs: modo de seleção (checkboxes na árvore) com barra de
  ações — mudar status, mover para pasta, excluir (→ lixeira) — com
  ConfirmModal resumindo N itens e toast de resultado (X ok / Y falhas).
- Executions: seleção múltipla com exclusão em lote (mesmo padrão).
- Cliente itera os endpoints unitários existentes (sem endpoint bulk novo);
  progresso simples durante o lote.

## Scope boundaries

- Sem endpoint bulk no backend na v1 (N chamadas; aceitável para N<100 —
  documentar; se doer, vira change própria).
- Sem bulk-edit de outros campos (tags, prioridade) na v1.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Selecionar N CTs e mudar status/mover/excluir aplica em todos com resumo; N executions excluídas em lote — build + revisão visual (endpoints unitários já testados).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
