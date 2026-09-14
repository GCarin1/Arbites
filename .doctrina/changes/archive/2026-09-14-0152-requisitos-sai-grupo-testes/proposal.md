# Change 0152-requisitos-sai-grupo-testes — requisitos sai do grupo Testes: ele e insumo do time de negocio e nao trabalho de QA, e sob aquele cabecalho o menu afirma o contrario

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** design-system

## Why

requisitos sai do grupo Testes: ele e insumo do time de negocio e nao trabalho de QA, e sob aquele cabecalho o menu afirma o contrario

## What

`Requisitos` estava dentro do grupo **Testes**, ao lado de Test cases e
Execuções. Mas epic e story nascem com o time de negócio — o que o QA faz é
**cobri-los**. Sob aquele cabeçalho o menu afirmava o contrário, e menu que
mente sobre de quem é a coisa ensina o modelo errado para quem chega.

`Requisitos` passa a ser item solto, **antes** dos grupos:

```
Hoje
Requisitos            ← insumo do negócio
TESTES                ← o trabalho de QA
  Test cases
  Execuções
ACOMPANHAMENTO
  …
```

**Antes e não depois** porque é a ordem do fluxo: requisito existe antes do
caso, que existe antes da execução. E **sem cabeçalho próprio** pela mesma
razão que a change 0129 registrou ao criar `NAV_LOOSE` para a IA: um título
de grupo para um item só ocupa uma linha inteira para dizer o que o próprio
item já diz. Se um dia houver mais de uma tela de negócio, o grupo nasce
então.

**Afeta spec:** `design-system` — a orientação e o agrupamento do menu são
dela.

## Scope boundaries

- Não muda nada dentro da tela de Requisitos: a árvore, a cobertura e as
  ações continuam as mesmas.
- Não cria grupo novo, e não mexe em "Mais" nem no rodapé.
- Não muda permissão: quem podia criar requisito continua podendo.

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
- [x] No menu, a ordem é Hoje → Requisitos → TESTES (Test cases, Execuções)
      → ACOMPANHAMENTO — conferido lendo o menu renderizado.
- [x] `Requisitos` não aparece mais sob nenhum cabeçalho de grupo.
- [x] O item continua fixável (pin) e navegável como antes.

## Open questions

Nenhuma.

## Nota sobre o gate de documentação

O passo `docs` barrou esta change apontando `NAV_LOOSE` como "variável de
ambiente". Não é: é uma constante de TypeScript em `App.tsx`, sem alcance
fora do arquivo. A heurística casa qualquer identificador em MAIÚSCULAS com
sublinhado, e todo `const` de módulo neste projeto é assim.

É a segunda vez que o gate erra desse jeito (a primeira foi com a custom
property `--heat-cell`, na change 0138). Padrão que vale registrar: o passo
`docs` acerta em endpoint público — como acertou na 0151, com
`DELETE /audit/{id}` — e erra em identificador interno. A change foi fechada
com `--force`, que registra a lacuna; esta nota é a lacuna por extenso.
