# Change 0104-autoria-pelo-usuario-logado — Autoria pelo usuario logado

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** profile

## Why

Com varios usuarios sobre o mesmo workspace, a identidade logada passa a preencher automaticamente a autoria: owner e author de executions, criador de requisitos, casos de teste e defeitos deixam de ser texto livre e passam a vir da sessao. O profile.md, hoje unico na raiz do workspace e global, passa a ser por usuario, preservando a memoria de IA individual sem vazar entre contas.

## What

- Delta MODIFIED em `profile`: perfil por conta e autoria pela sessão.
- `backend/arbites/api.py`: `_profile_path` por conta com herança única do
  arquivo da raiz; `owner` e `created_by` vindos da sessão.
- `backend/tests/test_authorship.py`.

## Scope boundaries

- A autoria é gravada no disco e sai nas respostas que já leem o arquivo;
  **não** é indexada nem filtrável nesta entrega. Quem precisa perguntar "o
  que fulano mexeu" usa o log de atividade do 0103, que já responde isso
  sem duplicar o dado no índice.
- Não migra artefato existente: quem foi criado antes fica sem `created_by`,
  porque inventar um autor retroativo seria pior que a ausência.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa com o novo
      `backend/tests/test_authorship.py`.
- [x] `npm --prefix frontend run build` passa.
- [x] Os 5 novos acceptance criteria de `profile` estão `[verified]`.
- [x] Com `ARBITES_AUTH=off` nada muda para a instalação de uma pessoa só.

## Open questions

Nenhuma. A herança do `profile.md` da raiz pela conta de menor id é uma
regra determinística escolhida porque essa conta é, por construção, o
usuário único que existia antes da instância virar multiusuário.
