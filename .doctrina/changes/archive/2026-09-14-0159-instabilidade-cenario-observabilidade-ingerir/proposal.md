# Change 0159-instabilidade-cenario-observabilidade-ingerir — instabilidade de cenario na observabilidade: ingerir o cucumber json por cenario do artifact e apontar o teste que virou instavel

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** reporting

## Why

instabilidade de cenario na observabilidade: ingerir o cucumber json por cenario do artifact e apontar o teste que virou instavel

## What

Fecha o vão que a change 0155 registrou: *"teste que virou instável"* ficou de
fora porque o manifesto declara medida **agregada**, e "2 cenários falharam"
não responde **qual** balança.

Instabilidade é por cenário, e não aparece em média nenhuma: um teste que
passa, falha e passa de novo some numa taxa de sucesso e continua corroendo a
confiança na suíte — que é o custo real, porque a partir de certo ponto
ninguém olha mais o vermelho.

O Cucumber JSON já vem no artifact e já é lido aqui (`behave_json.py`, e o
leitor da change 0148). Esta change o ingere **por cenário**, liga cada um ao
caso pela tag `@CT-XXXX` (ADR 0003) e calcula:

- **instável** = passou **e** falhou dentro do período;
- **virou instável** = estava estável no período anterior.

A segunda é a que vira anúncio. "Está instável" não é notícia para quem já
sabe; "virou" é. E **falhar sempre não é instabilidade** — isso é defeito, e
chamá-lo de instável faria alguém re-executar em vez de corrigir.

## Scope boundaries

- Não quarentena nem desabilita teste: apontar é o primeiro passo, agir é
  decisão de pessoa.
- Não muda o manifesto: `kind: cucumber` já era um anexo válido, e sem
  manifesto a convenção de nome resolve.

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
- [x] O Cucumber do artifact vira resultado por cenário, ligado ao caso pela tag.
- [x] Cenário que passa e falha no período aparece como instável.
- [x] Só quem estava estável antes entra em "o que mudou".
- [x] Cenário que falha sempre NÃO é chamado de instável.
- [x] O índice é reconstruível do disco.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
