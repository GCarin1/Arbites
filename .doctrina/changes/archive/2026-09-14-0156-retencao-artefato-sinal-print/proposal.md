# Change 0156-retencao-artefato-sinal-print — retencao de artefato e sinal: print e log de um cron diario enchem o disco e ninguem decidiu por quanto tempo guardar

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** runtime (confident; signals: log) — opened anyway (--force)
- **Affects specs:** reporting

## Why

retencao de artefato e sinal: print e log de um cron diario enchem o disco e ninguem decidiu por quanto tempo guardar

## What

Um cron diário com prints enche disco. Não é hipótese: é aritmética.

Esta change decide a retenção **junto** com a ingestão, e não depois. Deixar
para decidir depois é como se descobre o problema tarde — e é exatamente a
lacuna que ficou aberta na change 0151, com as rodadas de auditoria.

A regra que eu defenderia: **sinal e anexo têm valores de vida diferentes.**

- **Sinal** é barato e é o que faz série temporal: guarda-se por muito tempo.
- **Anexo** (print, log, artifact bruto) é caro e só interessa perto do
  evento: guarda-se por pouco, e some primeiro.

Ou seja, a série continua respondendo "a acessibilidade regrediu em agosto?"
mesmo depois do print daquele dia ter ido embora — que é o trade-off certo.

Retenção é **configuração**, com padrão explícito e visível na tela, não
número escondido no código. E apagar é para a lixeira, como todo o resto.

## Scope boundaries

- Não apaga resultado de teste nem execução: retenção aqui é de artefato de
  CI e sinal, não do trabalho do QA.
- Não decide sozinha na primeira execução: a primeira limpeza é anunciada
  antes de acontecer.

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
- [x] Sinal e anexo têm janelas de retenção independentes e configuráveis.
- [x] A tela mostra quanto está ocupado e o que a próxima limpeza levaria,
      antes de levar.
- [x] Anexo expirado some e a série temporal do mesmo período continua
      respondendo.
- [x] Limpeza é para a lixeira e é reversível enquanto a lixeira não é
      esvaziada.

## Open questions

Nenhuma.
