# Change 0123-upload-simultaneo-evidencia-responde — upload simultaneo de evidencia responde 201 mas perde parte dos registros no execution.json

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

upload simultaneo de evidencia responde 201 mas perde parte dos registros no execution.json

## What

- `executions` (spec MODIFIED): a proibição de suspender a requisição no
  meio do ciclo de leitura-alteração-escrita da execution.
- `backend/arbites/api.py`: a leitura do arquivo sai de dentro desse trecho.
- `backend/tests/test_executions_concurrency.py`: seis uploads simultâneos
  contra o app real, por ASGI, já que o cliente de teste síncrono serializa
  as requisições e não reproduziria a corrida.

## Scope boundaries

- Não introduz trava por execution: nenhuma outra rota de resultado suspende
  entre carregar e gravar, e travar por precaução esconderia a próxima que
  fizer isso em vez de impedi-la.
- Não muda o formato da evidência nem onde ela é gravada.
- Não limita o tamanho do upload de evidência, que é outra conversa.

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
