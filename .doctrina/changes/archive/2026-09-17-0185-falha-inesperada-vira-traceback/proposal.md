# Change 0185-falha-inesperada-vira-traceback — falha inesperada vira traceback cru na resposta em vez de erro legivel

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime (confident; signals: traceback) — opened anyway (--force)
- **Affects specs:** workspace-core

## Why

falha inesperada vira traceback cru na resposta em vez de erro legivel

## What

- `api.py`: `@app.exception_handler(Exception)` como rede de segurança.
  Responde `internal_error` com um identificador de rastreio, e manda o
  traceback completo para o log do servidor sob o mesmo identificador.
- A mensagem NÃO repassa `str(exc)`: uma exceção qualquer pode carregar
  caminho de arquivo, trecho de SQL ou pedaço de credencial, e essa resposta
  sai para o navegador.

## Scope boundaries

- Os erros já previstos (`CIError`, `ExecutionError`, `AuthError`, …)
  continuam com os handlers deles: a rede de segurança é o que sobra, não
  uma camada por cima.
- O traceback continua no log, inteiro. É onde ele serve — para quem vai
  corrigir —, e não na tela de quem só queria clicar num botão.

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
