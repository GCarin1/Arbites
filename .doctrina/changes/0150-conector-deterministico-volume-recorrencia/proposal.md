# Change 0150-conector-deterministico-volume-recorrencia — conector deterministico para volume e recorrencia empurrando ciclo fechado inteiro sem custar um turno de agente por item

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** integrations

## Why

conector deterministico para volume e recorrencia empurrando ciclo fechado inteiro sem custar um turno de agente por item

## What

O agente é a ponte certa para o fluxo com humano no meio: um card, uma
story, um caso — ambiguidade real, decisão humana no meio. Ele é a ponte
**errada** para volume.

"Empurrar os 47 resultados do ciclo que fechou" não deveria custar 47 turnos
de agente, não deveria custar 47 confirmações, e sobretudo não deveria variar
de uma execução para outra. Isso é trabalho determinístico: pega o conjunto,
compara com o vínculo, age no delta, registra.

Esta change entrega o transporte próprio, sobre a porta que a 0145 definiu e
que a 0148 já validou com um segundo adaptador:

- **empurrar um ciclo inteiro** (resultados + evidências) para o sistema
  ligado, em uma operação, com preview do delta antes;
- **reexecutável sem efeito colateral**: rodar duas vezes não duplica, porque
  a idempotência vem do vínculo e não da memória de quem chamou;
- **retomável**: falha no meio não deixa metade sincronizada sem registro —
  o que passou fica marcado, e a próxima tentativa continua de onde parou;
- **respeita limite de taxa** do sistema de destino, com recuo progressivo.

Continua valendo tudo da ADR 0015: capacidade declarada, o que não cabe é
recusado em voz alta, e conflito nunca é resolvido sozinho — ele sai do lote
e vai para Problemas, sem travar o resto.

**Afeta spec:** `integrations`. **ADR:** 0015.

## Scope boundaries

- Não substitui o MCP: fluxo com humano no meio continua sendo do agente.
  Este conector é para lote e recorrência.
- Não agenda sozinho: quem dispara é a pessoa ou um gatilho externo. O
  produto é local-first e não roda tarefa de fundo sem alguém pedir.
- Não inventa adaptador novo — usa a porta e os adaptadores existentes.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Empurrar o mesmo ciclo duas vezes não duplica nada no destino.
- [ ] Interromper no meio e repetir continua de onde parou, sem reenviar o
      que já tinha ido.
- [ ] Um artefato em conflito sai do lote com o motivo e o restante do lote
      segue.
- [ ] Resposta de limite de taxa faz o envio recuar e retomar, sem perder
      item.

## Open questions

Esta change só faz sentido depois que a 0145 a 0148 estiverem em uso real.
Se na prática o agente der conta do volume que você tem, ela pode não
precisar existir — e não construir é o melhor resultado possível para ela.
