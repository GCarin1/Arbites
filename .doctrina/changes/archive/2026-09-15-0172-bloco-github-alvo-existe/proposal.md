# Change 0172-bloco-github-alvo-existe — bloco github do alvo nao existe na UI e o dispatch responde 422 sem dizer o que falta, e salvar pela tela apaga o bloco escrito a mao

- **Status:** applied
- **Applied:** 2026-09-15
- **Date:** 2026-09-15
- **Owner:** Gcarini
- **Lane:** runtime (confident; signals: dispatch) — opened anyway (--force)
- **Affects specs:** ci-automation

## Why

bloco github do alvo nao existe na UI e o dispatch responde 422 sem dizer o que falta, e salvar pela tela apaga o bloco escrito a mao

## What

- `backend/arbites/api.py`: `GithubTargetIn` (repo/workflow/ref) entra em
  `AutomationTargetIn`, e `_targets_out` devolve o bloco. Era a ausência do
  campo no modelo que fazia o `model_dump` do PUT apagar o que estava no YAML.
- `PUT /targets` descarta bloco pela metade em vez de gravá-lo.
- `backend/arbites/ci.py`: a recusa do disparo passa a nomear a tela onde se
  configura, não a chave do arquivo.
- `frontend/src/components/Automation.tsx`: três campos novos no formulário
  do alvo (Repositório, Workflow, Branch), carregados e salvos junto.
- README: o aviso de defeito conhecido vira a descrição do comportamento.

## Scope boundaries

- O PAT continua fora do `arbites.yaml`: ele mora no keyring do SO ou em
  `ARBITES_GITHUB_TOKEN` (ADR 0008/0017). Aqui só entra onde disparar, nunca
  com que credencial.
- A correlação do run disparado e a coleta do artifact não mudam.

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
