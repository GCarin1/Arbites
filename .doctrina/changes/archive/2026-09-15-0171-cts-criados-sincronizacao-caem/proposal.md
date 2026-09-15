# Change 0171-cts-criados-sincronizacao-caem — CTs criados pela sincronizacao de feature caem todos numa pasta so em vez de espelhar a arvore dos arquivos

- **Status:** applied
- **Applied:** 2026-09-15
- **Date:** 2026-09-15
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** local-automation

## Why

CTs criados pela sincronizacao de feature caem todos numa pasta so em vez de espelhar a arvore dos arquivos

## What

- `backend/arbites/feature_sync.py`: `prefixo_estatico(glob)` (a parte antes
  do primeiro curinga — `features/` em `features/**/*.feature`) e
  `pasta_do_cenario(feature_path, glob)`, que devolve a subpasta espelhando a
  árvore, com o nome do arquivo `.feature` como folha.
- `backend/arbites/api.py`: `features-sync/apply` resolve o diretório por
  item em vez de uma vez só; `payload.folder` passa a ser a RAIZ do espelho,
  não o destino final.

## Scope boundaries

- CTs já criados não são movidos: o caminho de um artefato é estável e mexer
  nele quebraria links e histórico. A árvore nova vale para o que vier.
- Sem colapso quando pasta e arquivo têm o mesmo nome
  (`login/login.feature` → `login/login/`): a regra vale igual para todo
  caminho, e o destino segue previsível quando um segundo `.feature` aparece
  ao lado.

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
