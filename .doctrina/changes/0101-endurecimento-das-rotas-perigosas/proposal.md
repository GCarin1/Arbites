# Change 0101-endurecimento-das-rotas-perigosas — Endurecimento das rotas perigosas

- **Status:** proposed
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** runtime (confident; signals: runner, segredos) — opened anyway (--force)
- **Affects specs:** workspace-core

## Why

Restringir as rotas que executam codigo ou expoem segredos antes de o Arbites ficar acessivel pela internet: runner local (POST /runs/local), navegacao de filesystem (/automation/browse-features), leitura e escrita do .env dos targets, token do GitHub e chaves de IA, e import Xray. Cada uma passa a exigir papel admin e a respeitar um kill switch persistido que o admin liga e desliga, com o estado exposto na API para a UI esconder o que esta desligado.

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
