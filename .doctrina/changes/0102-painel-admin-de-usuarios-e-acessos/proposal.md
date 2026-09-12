# Change 0102-painel-admin-de-usuarios-e-acessos — Painel admin de usuarios e acessos

- **Status:** proposed
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** runtime (confident; signals: log) — opened anyway (--force)
- **Affects specs:** admin

## Why

Painel administrativo no frontend, visivel apenas para o papel admin, com duas abas iniciais: Usuarios (lista com papel, status, ultimo login e data de criacao; acoes de aprovar ou recusar cadastro pendente, ativar e desativar, trocar papel, forcar reset de senha e encerrar sessoes ativas; nunca deletar, para preservar a autoria historica) e Acessos (fila de cadastros pendentes mais o log de autenticacao com login bem sucedido, login falho, IP real lido de CF-Connecting-IP, user-agent e data). Inclui a aba Sistema com estado do indice, tamanho da lixeira, versao e os kill switches.

## What

<!-- The shape of the change: artifacts created or modified, specs affected. -->

## Scope boundaries

<!-- Anything adjacent that this change deliberately does NOT touch. -->

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
