# Change 0103-log-central-de-atividade — Log central de atividade

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (uncertain; signals: requisito)
- **Affects specs:** audit

## Why

Log central de escrita respondendo quem fez o que e quando: criacao, edicao e exclusao de requisito, caso de teste, execution e defeito, disparo de automacao, alteracao de .env e de token. Cada entrada guarda usuario, acao, alvo, data e IP; a consulta e paginada e filtravel por usuario, acao e periodo, exposta ao papel admin e alimentando a aba Atividade do painel. Reaproveita o padrao de eventos que ja existe no historico das executions.

## What

- Delta MODIFIED em `audit`: o log contínuo de escrita, ao lado das rodadas
  de qualidade que já existiam.
- `backend/arbites/auth.py`: tabela `activity` no banco durável, escrita e
  consulta filtrável.
- `backend/arbites/api.py`: registro no gate, depois da resposta, para toda
  escrita bem-sucedida; rota `GET /admin/activity`.
- `frontend/src/components/Admin.tsx`: aba Atividade.
- `backend/tests/test_activity_log.py`.

## Scope boundaries

- Não registra leitura: o volume afogaria o sinal e GET não altera nada.
- Não registra corpo de requisição — ver o must-not da spec.
- Não substitui as rodadas de auditoria de qualidade; são coisas diferentes
  na mesma capability.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa com o novo
      `backend/tests/test_activity_log.py`.
- [x] `npm --prefix frontend run build` passa.
- [x] Os 4 novos acceptance criteria de `audit` estão `[verified]`.
- [x] O log registra uma rota de escrita que ninguém anotou à mão, provado
      por um teste que exercita uma rota qualquer e confere a entrada.

## Open questions

Nenhuma.
