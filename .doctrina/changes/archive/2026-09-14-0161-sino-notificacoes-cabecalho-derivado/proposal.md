# Change 0161-sino-notificacoes-cabecalho-derivado — sino de notificacoes no cabecalho derivado do estado vivo: problemas, observabilidade, acoes do sistema e log info para admin, com lido nao lido por usuario e navegacao para a origem

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (confident; signals: log) — opened anyway (--force)
- **Affects specs:** reporting

## Why

sino de notificacoes no cabecalho derivado do estado vivo: problemas, observabilidade, acoes do sistema e log info para admin, com lido nao lido por usuario e navegacao para a origem

## What

Um sino no cabeçalho, à direita da busca, com a contagem de não lidas no
próprio ícone. É a evolução do que a aba **Problemas** já fazia — e Problemas
continua existindo: o sino é ambiente, a aba é triagem (e tem a lixeira).

**A decisão que manda em tudo: a lista é DERIVADA do estado vivo.** Não é uma
caixa de entrada. Ela é calculada a cada leitura das fontes que já são
verdade, e o que se grava por pessoa é só *o que eu li* e *até onde limpei*.

A consequência é deliberada e foi escolhida com o Gcarini: **um problema
resolvido some do sino mesmo sem ter sido lido**, porque deixou de existir.
Uma caixa de entrada gravada criaria um segundo estado, e o segundo diverge do
primeiro — o aviso corrigido ficaria na lista, alguém clicaria e não acharia
nada. Esse defeito exato já apareceu aqui (story sem epic dada como
descoberta, change 0158) e é o pior tipo, porque parece informação.

Cada notificação tem **id estável** (hash da origem + chave), então "lido"
gruda quando a lista inteira é recalculada do zero.

**Quatro origens**, e a fronteira entre elas é sobre quem estava olhando:

- `problema` — avisos do índice e da credencial;
- `observabilidade` — o que mudou sozinho: quebrou, virou instável, silêncio
  da ingestão, sinal que regrediu;
- `feito` — ação do **sistema** que deu certo: ingestão trouxe execuções,
  auditoria rodada, ciclo fechado. "Criei um CT agora" NÃO entra: você já
  sabe que clicou;
- `info` — o log de atividade, só admin e só com interruptor. Nasce
  desligado: é o único volume capaz de inundar a lista.

Junto: **Automação passa para a seção Testes**. Rodar o teste é trabalho de
teste. A ADR 0012 congelou a PERIFERIA para focar em repositório, ciclo e
execução — automação é o braço da execução, então ela estava do lado errado
da régua, não do lado certo.

## Scope boundaries

- Não remove a aba Problemas: ela é a página de triagem e guarda a lixeira.
- Não notifica por e-mail nem push: é um produto local, e o sino é a
  superfície.
- Não abre websocket: uma consulta por minuto basta num produto local-first.

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
- [x] Problema resolvido sai do sino mesmo sem ter sido lido.
- [x] O sino e a aba Problemas leem a MESMA lista.
- [x] Clicar leva ao item, não à lista dele.
- [x] O nome do arquivo vem separado da frase, e não aparece duas vezes.
- [x] Lido é por pessoa e sobrevive ao recálculo (id estável).
- [x] Limpar é marca d'água: não apaga o motivo, que volta se voltar a
      acontecer.
- [x] Log de atividade só alcança admin, e só com o interruptor ligado.
- [x] Em 390 px o painel cabe na tela e o texto quebra.

## Open questions

**Dois defeitos encontrados medindo no navegador, não em teste:**

1. O `button` global é `white-space: nowrap` com altura fixa — desenhado para
   rótulo curto. O corpo da notificação é um `button` (para ser clicável por
   inteiro) e leva uma FRASE: sem desfazer os dois, o texto virava uma linha
   só, estourava o painel e empurrava o "lida" para fora.
2. Em 390 px eu tinha tornado `.sino` estático para o painel ancorar na tela.
   Isso tirou a referência do `top: 100%`, que passou a valer sobre a página
   inteira e jogou o painel para baixo da dobra — ele estava lá, invisível,
   com as coordenadas horizontais certíssimas. `position: fixed` mede a
   viewport e não depende de ancestral nenhum.

Os dois só apareceram porque a medição é no navegador, e nenhum teste de API
os pegaria.

<!-- List unresolved decisions. Empty if none. -->
