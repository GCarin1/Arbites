# Change 0162-acoes-sino-liam-como — acoes do sino liam como palavras soltas: marcar todas como lidas parecia quatro links por causa da fonte monoespacada sem contorno

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** reporting

## Why

acoes do sino liam como palavras soltas: marcar todas como lidas parecia quatro links por causa da fonte monoespacada sem contorno

## What

No cabeçalho do sino, "Marcar todas como lidas" era lido como **quatro coisas
distintas**, e não como uma ação — ainda mais ao lado de "Limpar", que é outra.

A causa é o `.link-btn`: monoespaçado e sem contorno. Em fonte monoespaçada
cada palavra ocupa uma largura regular e nenhuma se liga à seguinte; sem
contorno, nada diz onde a ação começa e termina. Quatro palavras azuis em fila
são quatro alvos de clique aos olhos de quem chega.

A correção não é encurtar o rótulo — encurtar esconde o sintoma e o problema
volta na próxima frase de três palavras. É dar **contorno** à ação e usar
fonte proporcional: aí a frase vira um botão só, independente de quantas
palavras tenha.

O mesmo vale, menor, para o "lida / não lida" de cada item: "não lida" em mono
azul são duas palavras que leem como dois links.

## Scope boundaries

- Não muda o `.link-btn` das outras telas: lá ele é usado em ações de UMA
  palavra, onde a ambiguidade não aparece. Trocar todas de uma vez seria
  mexer em telas que ninguém reclamou.

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
- [x] "Marcar todas como lidas" lê como um botão só, com contorno próprio.
- [x] "não lida" no item também é um selo único.
- [x] Em 390 px as três ações continuam cabendo sem quebrar a linha.

## Open questions

**Onde mais isso pode estar:** o `.link-btn` monoespaçado é usado em outras
telas. Ali ele aparece em ações de uma palavra ("abrir", "restaurar"), onde a
ambiguidade não surge — por isso não mexi. Mas a regra vale em geral: ação de
várias palavras precisa de contorno. Se aparecer outro rótulo longo em
`link-btn`, é o mesmo defeito.

<!-- List unresolved decisions. Empty if none. -->
