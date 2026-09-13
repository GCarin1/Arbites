# Change 0100-autenticacao-de-sessao — Autenticacao de sessao

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (confident; signals: introduzir, para que)
- **Affects specs:** auth

## Why

Introduzir autenticacao no Arbites para que ele possa ser exposto fora da maquina local: tela de login, sessao por cookie httpOnly SameSite=Lax, senhas com Argon2, cadastro aberto que nasce pendente de aprovacao do admin, bootstrap do primeiro admin por variavel de ambiente, rate limit e lockout no login, e gate de autenticacao em todas as rotas da API exceto as de login/cadastro e os estaticos do SPA. Papeis admin/editor/viewer sobre um workspace compartilhado unico.

## What

- Capability nova `auth` (`.doctrina/specs/auth/spec.md`) — identidade,
  sessão, cadastro com aprovação, gate da API.
- `.doctrina/product.md`: autenticação sai de "Out of scope" e entra no
  escopo; novo critério SC15; milestone M14 na ordem de entrega.
- ADR 0011 — contas e sessões num banco durável `.arbites/auth.db`, fora da
  fonte de verdade em filesystem (ADR 0001) e fora do índice descartável.
- `backend/arbites/auth.py` (novo): schema, hash Argon2id, sessões,
  lockout, bootstrap do admin.
- `backend/arbites/api.py`: rotas `/auth/*` e middleware de gate.
- `frontend/src/components/Login.tsx` (novo) + guarda de sessão no
  `App.tsx`.
- `backend/requirements.txt`: `argon2-cffi`.

## Scope boundaries

Deliberadamente fora deste change, cada um no seu:

- Papel exigido por rota e kill switches das rotas perigosas — 0101.
- Painel admin de usuários e a leitura do log de acesso — 0102.
- Log central de escrita — 0103.
- Autoria de artefato pela sessão e `profile.md` por usuário — 0104.
- Docker e Cloudflare Tunnel — 0105.

Este change autentica e recusa anônimo; ele ainda **não** distingue o que
um `editor` pode fazer e um `viewer` não. Até o 0101 fechar, papel é um
campo gravado e exposto, não um limite aplicado.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa, incluindo o novo
      `backend/tests/test_auth.py`.
- [x] `npm --prefix frontend run build` passa com a tela de login.
- [x] Os 7 acceptance criteria da spec `auth` estão `[verified]` e citam
      o teste que os prova (`doctrina coverage`).
- [x] A suíte pré-existente continua verde sem alteração de teste que
      afrouxe asserção — os testes antigos passam a autenticar.

## Open questions

Nenhuma. As três bifurcações foram decididas com o usuário antes de abrir o
change: workspace compartilhado com papéis, cadastro aberto pendente de
aprovação, autenticação na própria aplicação (sem Cloudflare Access e sem o
proxy do BFFless).
