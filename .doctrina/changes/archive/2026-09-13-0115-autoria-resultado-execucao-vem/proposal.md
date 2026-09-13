# Change 0115-autoria-resultado-execucao-vem — autoria do resultado de execucao vem da sessao e nao do corpo da requisicao

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** executions

## Why

autoria do resultado de execucao vem da sessao e nao do corpo da requisicao

## What

- `executions` (spec MODIFIED): autoria de resultado vem da sessão, e `who`
  sai do contrato de entrada.
- `backend/arbites/api.py`: `author_of(request)` nas quatro rotas de escrita
  em resultado; `who` recusado com 422.
- `backend/tests/test_authorship_executions.py`: a prova dos dois critérios.
- `frontend/src/components/Executions.tsx`: para de mandar `who`.

## Scope boundaries

- Não mexe na autoria de requisito, caso de teste e defeito, que já vem da
  sessão desde a change 0104.
- Não reescreve `execution.json` antigo: resultado gravado como `local` no
  passado continua como está — o histórico registra o que aconteceu, não o
  que deveria ter acontecido.
- Não muda quem PODE escrever (isso é a capability `auth`); muda apenas com
  que nome a escrita é assinada.

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
