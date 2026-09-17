# Change 0177-marca-dagua-ingestao-conta — marca dagua da ingestao conta anexo markdown como run ja ingerido

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

marca dagua da ingestao conta anexo markdown como run ja ingerido

## What

- `backend/arbites/ci_ingest.py`: `ja_ingeridos()` passa a olhar só
  `ci/<ano>/*.md`, e não `ci/**/*.md`. O `rglob` entrava em
  `ci/<ano>/<chave>/`, a pasta de anexos, onde mora o `analysis.md` que o
  pipeline publica.
- Mesma passagem: `"1 execução verde seguidas"` — o `plural()` trocava o
  substantivo e deixava o adjetivo no plural. Agora os dois concordam.

## Scope boundaries

- A marca d'água continua derivada do disco, não guardada: um contador
  "último run visto" mente na primeira falha no meio (ADR 0016). O defeito
  era o alcance da varredura, não o princípio.

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
