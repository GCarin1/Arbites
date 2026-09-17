# Change 0178-erros-repositorio-origem-disparou — erros por repositorio de origem que disparou a suite de teste

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** ci-automation

## Why

erros por repositorio de origem que disparou a suite de teste

## What

- `ci_ingest.normalizar_gatilho`: lê o bloco `trigger` do manifesto (com
  nomes alternativos de campo) e cai no rótulo `repo_origem`/`source_repo`
  quando ele não existe — quem já usa `labels` não migra nada.
- `indexer`: `ci_runs` ganha `trigger_repo`, `trigger_environment` e
  `trigger_ref`, com migração tolerante.
- `ci_ingest.por_origem` e `erros_por_origem`; o painel devolve `by_origin` e
  `errors_by_origin`.
- `Observability.tsx`: pizza de erros por repositório de origem, tabela de
  saúde por origem, e a nota que explica por que há dois recortes.

## Scope boundaries

- Nada é inferido do nome do repositório ou do evento do GitHub: a topologia
  é declarada. Adivinhar erraria na primeira exceção, e uma origem errada é
  pior que nenhuma — ela manda o time olhar o produto errado.

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
