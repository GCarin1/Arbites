# Change 0122-progresso-ciclo-conta-status — progresso do ciclo conta por status enquanto o quadro conta por coluna e os dois numeros divergem

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

progresso do ciclo conta por status enquanto o quadro conta por coluna e os dois numeros divergem

## What

- `executions` (spec MODIFIED): o progresso do ciclo passa a ser apurado
  pela coluna, e o cabeçalho a exibir o que o servidor apurou.
- `backend/arbites/executions.py`: `progress()` conta por `column || status`.
- `frontend/src/components/Executions.tsx`: o cabeçalho consome
  `execution.progress` em vez de manter a segunda contagem.
- `backend/tests/test_execution_cycle.py`: a prova com um caso arrastado.

## Scope boundaries

- Não mexe na separação entre status e coluna, que é a ADR 0005 e continua
  valendo: o que muda é qual dos dois o progresso conta.
- Não toca no `result_counts` da lista, que vem do índice e responde outra
  pergunta (quantos casos em cada status registrado).
- Não muda a barra empilhada nem os contadores do Kanban, que já contavam
  pela coluna.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

Nenhuma.
