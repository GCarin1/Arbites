# Change 0169-tela-troca-senha-obrigatoria — tela de troca de senha obrigatoria nunca aparece e a sessao acaba entrando no app com todas as chamadas em 403

- **Status:** applied
- **Applied:** 2026-09-15
- **Date:** 2026-09-15
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** auth

## Why

tela de troca de senha obrigatoria nunca aparece e a sessao acaba entrando no app com todas as chamadas em 403

## What

Três defeitos encadeados, todos na ponte entre o gate e a tela.

- `frontend/src/components/AuthGate.tsx`: `<Login>` ganha `key` por fase. Sem
  ela o React reaproveitava a mesma instância vinda da fase anônima, e o
  `useState` que escolhe o modo "password" não roda de novo — a tela
  continuava em "Entrar" como se o login não tivesse acontecido.
- `AuthGate.tsx`: a fase de troca deixa de marcar `authenticated` por decreto
  e passa a rotear por `user.must_change_password`. Era isso que, na segunda
  tentativa de login, montava o app inteiro com a obrigação pendente.
- `frontend/src/api.ts` + `AuthGate.tsx`: `password_change_required` ganha um
  canal próprio (`onPasswordChangeRequired`), como o 401 já tinha, e devolve a
  SPA à tela de troca — a obrigação pode nascer com o app montado.
- `frontend/src/components/Profile.tsx`: cartão **Senha** no Perfil, para
  trocar a própria senha a qualquer momento (`POST /auth/password`).
- `backend/tests/test_troca_obrigatoria.py` fixa o contrato que a tela
  consome: `must_change_password` no login e no `/auth/me`, e o código
  `password_change_required` na recusa.

## Scope boundaries

- O backend não muda: o gate, os códigos e as três rotas de saída já estavam
  certos. O defeito era inteiramente da ponte com a tela.
- Recuperar senha esquecida sem sessão continua fora: a saída é local
  (`python -m arbites admin`), por não haver canal de e-mail nesta instalação.

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
- [x] Reproduzido no navegador ANTES da correção: primeiro login volta a
      "Entrar"; o segundo monta o app com 403 em `/workspace`, `/tree`,
      `/warnings`, `/runs/active`, `/executions`, `/defects`, `/todos`,
      `/daily`, `/notifications` e `/admin/switches`.
- [x] Depois da correção, no navegador: o login abre "Definir uma senha" com
      os três campos, a troca entra no app com **zero** 403, e uma sessão já
      dentro do app volta à troca quando a obrigação nasce no banco.
- [x] Cartão Senha do Perfil troca a senha de verdade, a 390px e a 1280px,
      sem estouro horizontal.

## Open questions

Nenhuma.
