# Change 0173-origens-observabilidade-so-existem — origens da observabilidade so existem no yaml e nao ha onde declara-las pela tela

- **Status:** applied
- **Applied:** 2026-09-15
- **Date:** 2026-09-15
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** ci-automation

## Why

origens da observabilidade so existem no yaml e nao ha onde declara-las pela tela

## What

- `backend/arbites/api.py`: `GET/PUT /ci/sources` (modelos
  `ObservabilitySourceIn`/`ObservabilitySourcesIn`), escrevendo o bloco
  `observability` do `arbites.yaml` — mesmo padrão de `PUT /ai/providers`.
  Escrever é `admin` na tabela de superfícies governadas; ler continua aberto,
  porque a tela precisa dizer "nenhuma origem" a quem não pode declarar.
- `frontend/src/components/Observability.tsx`: seção **Origens** com
  repositório, workflow e artifact, lista do que está declarado e remoção.
  Ela aparece quando não há dado nenhum — que é justamente quando importa.
- `frontend/src/api.ts` + `types.ts`: `ciSources`/`ciSourcesSave` e `CiSource`.

## Scope boundaries

- O PAT continua fora do YAML (ADR 0008/0017): aqui entra de onde puxar,
  nunca com que credencial.
- O formato do `arbites.json` e a ingestão em si não mudam.

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
