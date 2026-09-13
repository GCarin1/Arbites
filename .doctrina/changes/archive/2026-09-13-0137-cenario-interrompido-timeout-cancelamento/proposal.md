# Change 0137-cenario-interrompido-timeout-cancelamento — cenario interrompido por timeout ou cancelamento e gravado como passed porque o fecho do progresso ao vivo trata ausencia de falha como aprovacao

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** runtime (confident; signals: timeout) — opened anyway (--force)
- **Affects specs:** local-automation

## Why

cenario interrompido por timeout ou cancelamento e gravado como passed porque o fecho do progresso ao vivo trata ausencia de falha como aprovacao

## What

O progresso ao vivo (0076) lê o stream `plain` do behave e, ao ver um
cenário NOVO, fecha o anterior: se nenhum passo do cenário anterior falhou,
grava `passed`. `_collect` chama esse mesmo fecho uma última vez, para não
perder o último cenário do run.

Só que `_collect` roda também **depois de matar o processo** por timeout ou
cancelamento. Aí o "último cenário" é o que estava no meio de um passo
quando o processo morreu — e "não vi falha" nele não quer dizer que passou,
quer dizer que não terminou. Resultado: um caso que nunca chegou ao fim
aparece verde na execution. Numa plataforma de rastreabilidade de teste esse
é o pior defeito possível — o falso positivo mais caro que existe.

Depois disso, `_mark_pending(run, "blocked", "timeout")` não consertava: ele
só mexe em resultado **pendente**, e o caso já não estava mais pendente.

O conserto:

- `backend/arbites/runner.py` — `_live_conclude` passa a receber
  `interrupted`; com ele ligado, descarta o cenário aberto em vez de
  concluí-lo. `_collect` propaga, e `_run_one` liga quando `timed_out or
  cancelled`. O caso volta a chegar pendente em `_mark_pending`, que o marca
  `blocked` com `error: "timeout"`, como a spec já mandava.
- `backend/tests/test_local_runs.py` — teste novo que prende o
  comportamento pelo nome do defeito: cenário morto no meio não vira
  `passed`.

**Afeta spec:** `local-automation` — o requisito de timeout já existia
("marcar os resultados pendentes como `blocked`"); faltava dizer que um
cenário interrompido não produz resultado, que é a premissa que fazia o
requisito valer.

### Por que isto aparece agora

O defeito é antigo e estava calado: com a versão de behave que o container
tinha antes, a linha do cenário não chegava ao parser dentro dos 3 s do
teste, e o fecho não tinha o que concluir. O container foi reciclado, o
`behave` voltou numa versão que descarrega o stream mais cedo, e o mesmo
código passou a gravar o `passed`. A suíte não mudou — ela só parou de ter
sorte.

## Scope boundaries

- Não mexe no parser do Cucumber JSON (`behave_json.py`), que continua sendo
  a fonte oficial do resultado quando o run termina inteiro.
- Não mexe na fila, no SSE, nem no cálculo do timeout em si.
- Não declara nem fixa a versão do `behave` — a dependência de teste não
  declarada é um problema real, mas é outra change.

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
- [x] `test_timeout_marks_pending_as_blocked` volta a passar: o caso do
      cenário de 30 s, morto aos 3 s, chega `blocked` com `error: "timeout"`.
- [x] O teste novo falha contra o código antigo e passa contra o novo —
      conferido revertendo o `interrupted` e vendo o `passed` voltar.

## Open questions

Nenhuma.
