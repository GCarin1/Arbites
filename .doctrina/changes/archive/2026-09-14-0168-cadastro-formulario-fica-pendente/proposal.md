# Change 0168-cadastro-formulario-fica-pendente — cadastro pelo formulario fica pendente mesmo sem nenhum admin ativo para aprovar, e a tela nao avisa disso

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** auth

## Why

cadastro pelo formulario fica pendente mesmo sem nenhum admin ativo para aprovar, e a tela nao avisa disso

## What

Uma instância sem nenhum admin ativo passa a contar isso e a ter saída.

- `backend/arbites/auth.py`: `owner_email_from_env`, `no_active_admin` e
  `claims_instance` — o cadastro vira dono só quando não há admin ativo E o
  e-mail é o declarado em `ARBITES_ADMIN_EMAIL`.
- `backend/arbites/api.py`: `POST /auth/register` cria `admin`/`active` nesse
  caso (e devolve `admin: true`); `GET /auth/me` passa a responder `no_admin`
  e `owner_declared` a quem ainda não tem sessão.
- `frontend/src/components/Login.tsx` + `AuthGate.tsx` + `styles.css`: aviso
  na tela de login com a saída certa — cadastrar-se com o e-mail do ambiente,
  ou o comando `python -m arbites admin` quando não há nada declarado.
- ADR 0018 registra a revelação deliberada de `no_admin` e o limite da posse.
- `backend/tests/test_primeiro_dono.py` prova as duas saídas e os limites.

## Scope boundaries

- `bootstrap_admin` fica como está: continua agindo só no arranque e continua
  **não** sobrescrevendo a senha de uma conta que já existe.
- O 401 de login segue indistinguível de fora (conta inexistente, pendente,
  desativada e senha errada respondem igual) — nada aqui o afrouxa.
- O comando local `python -m arbites admin` (change 0166) não muda.

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
