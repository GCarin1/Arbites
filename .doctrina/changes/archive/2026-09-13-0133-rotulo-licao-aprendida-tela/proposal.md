# Change 0133-rotulo-licao-aprendida-tela — rotulo licao aprendida na tela de defeitos e lido como algo de pessoas em vez de causa raiz correcao e prevencao

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** defects

## Why

rotulo licao aprendida na tela de defeitos e lido como algo de pessoas em vez de causa raiz correcao e prevencao

## What

- `defects` (spec MODIFIED): o nome exibido do conjunto causa/correção/
  prevenção.
- `frontend/src/components/Defects.tsx`: filtro, marca e formulário.
- `frontend/src/components/AiAssist.tsx` e `Memory.tsx`: o mesmo
  vocabulário, para não haver dois nomes para a mesma coisa.

## Scope boundaries

- Não toca no frontmatter (`root_cause`, `fix`, `prevention`,
  `lesson_when`, `lesson_procedure`, `lesson_antipattern`): eles estão nos
  `.md` de workspaces existentes e renomeá-los quebraria dado gravado.
- Não muda `GET /defects?has_lesson=true` nem as colunas do índice, que
  estão documentados e em uso.
- Não remove o recurso: ele é o que impede a IA de repetir um bug já
  conhecido.

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
