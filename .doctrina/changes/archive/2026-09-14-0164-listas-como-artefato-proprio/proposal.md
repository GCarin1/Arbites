# Change 0164-listas-como-artefato-proprio — listas de to do como artefato proprio com vinculo um a um entre afazer e linha da lista, e borda do afazer pela cor do status

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** todos

## Why

listas de to do como artefato proprio com vinculo um a um entre afazer e linha da lista, e borda do afazer pela cor do status

## What

Duas referências, duas coisas diferentes — e a diferença É o desenho:

- **Afazer** é a nota adesiva (Sticky Notes): uma coisa a fazer, com prazo,
  status e **cor**. Nasce solta, num impulso, e é sobre ela que o sino cobra
  prazo.
- **Lista de To Do** é o roteiro (Microsoft To Do): passos que só fazem
  sentido juntos, com prazo **da lista**.

A linha da lista **não tem prazo próprio**, e é isso que dá sentido ao
vínculo: quando uma linha precisa de prazo, de status e de aparecer no sino,
ela se liga a um afazer. **O afazer traz a data; a linha traz o passo.**

**O vínculo é um-para-um e mora num lado só** — na linha. Guardar dos dois
lados abriria a chance de eles se contradizerem, e aí alguém teria de decidir
qual está certo sem ter como. O sentido inverso ("de que linha este afazer
participa") é uma CONSULTA, não um segundo dado.

Sobre a **cor da borda**: ela já existia, como uma faixa de 3 px à esquerda —
e passava despercebida, que na prática é o mesmo que não existir. A cor agora
vai na borda inteira e num tom de fundo, como uma nota adesiva de verdade, com
transição para a mudança de status ser VISTA.

## Scope boundaries

- Não move o afazer para dentro da lista: são artefatos diferentes, com
  ciclos de vida diferentes. Apagar a lista não apaga os afazeres.
- Não implementa "My Day", repetição nem lembrete por hora: o produto é
  local e não roda tarefa de fundo (ADR 0012).

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
- [x] A lista vira arquivo com id próprio, linhas e progresso.
- [x] O id de uma linha nunca é reaproveitado.
- [x] Um afazer se vincula a UMA linha, e a recusa nomeia a lista ocupada.
- [x] O afazer sabe de que linha participa sem o vínculo ser gravado duas
      vezes, e isso sobrevive ao reindex.
- [x] Lista com prazo e linha aberta aparece no sino; sem linha aberta ou
      arquivada, não.
- [x] A borda do afazer muda de cor com o status.
- [x] Em 390 px a tela não rola de lado.

## Open questions

**Um defeito que o teste pegou no meu próprio código:** o id da linha era
deduzido das linhas existentes (`max + 1`). Apagar a última linha fazia o
número RECUAR, e o id voltava a ser emitido — um afazer vinculado passaria a
apontar para uma linha que não é a dele, sem ninguém ser avisado, porque nada
falha. O contador passou a morar no arquivo e nunca recua.

**Dois defeitos de layout, ambos o `button` global:** ele centraliza o
conteúdo e `.list-toolbar button` tem `flex: 1`. O texto da linha saiu
centralizado e o botão "Nova lista" esticou de ponta a ponta. É a terceira vez
nesta sessão que o estilo global de botão colide com um uso novo — vale como
sinal de que ele está desenhado para rótulo curto e centralizado, e que todo
uso fora disso precisa desfazê-lo de propósito.

<!-- List unresolved decisions. Empty if none. -->
