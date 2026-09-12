# Change 0105-empacotamento-docker-e-cloudflare-tunnel — Empacotamento Docker e Cloudflare Tunnel

- **Status:** proposed
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (confident; signals: build, documentar) — opened as chore
- **Affects specs:** (none — chore)

## Why

Empacotar o Arbites como imagem Docker (build do frontend, FastAPI servindo o dist, workspace e banco em volume) mais um docker-compose pronto para UmbrelOS, e documentar a exposicao por hostname proprio no Cloudflare Tunnel apontando para a porta interna do container. Inclui as variaveis de ambiente de bootstrap do admin e do segredo de sessao, e a nota de por que a aplicacao nao passa pelo proxy do BFFless.

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
