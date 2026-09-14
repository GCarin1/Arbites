# Change 0163-sino-avisava-sobre-afazer — sino nao avisava sobre afazer vencido nem sobre afazer que vence hoje

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** reporting

## Why

sino nao avisava sobre afazer vencido nem sobre afazer que vence hoje

## What

O sino nasceu (change 0161) com quatro origens e **nenhuma olhava para
prazo** — sendo que o produto tem prazo desde sempre. Um afazer marcado para
hoje não avisava nada, e um vencido também não.

Um aviso que chega depois do prazo não é aviso.

Duas severidades, porque são duas situações: **vencido é problema** (já
passou), **vence hoje é atenção** (ainda dá tempo).

Duas decisões pequenas que mudam como o aviso se comporta:

- **O id inclui o dia de hoje.** Um afazer vencido volta a não-lido a cada dia
  que passa. Silenciar para sempre algo que está vencido é o contrário do que
  um lembrete faz — quanto mais atrasado, mais deve incomodar, não menos.
- **O instante do aviso é HOJE, não o prazo.** Com o prazo no passado, a marca
  d'água de "limpar" o esconderia para sempre.

## Scope boundaries

- Não avisa com antecedência: só vencido e hoje, como o Microsoft To Do.
  Avisar antes encheria a lista de coisa sobre a qual ninguém vai agir hoje.

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
- [x] Afazer que vence hoje aparece, com "vence HOJE" na frase.
- [x] Afazer vencido aparece como problema, dizendo há quantos dias.
- [x] Afazer concluído ou futuro não aparece.
- [x] O aviso de vencido volta a não-lido no dia seguinte.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
