# Change 0170-run-local-cria-execution — run local cria execution vazia e a falha de arranque do processo nao chega em lugar nenhum

- **Status:** applied
- **Applied:** 2026-09-15
- **Date:** 2026-09-15
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** local-automation

## Why

run local cria execution vazia e a falha de arranque do processo nao chega em lugar nenhum

## What

- `backend/arbites/runner.py`: `resolver_python()` + `PythonPathError`. Vazio
  usa o Python do Arbites; pasta de virtualenv é resolvida
  (`Scripts/python.exe`, `bin/python`); arquivo não-executável, pasta sem
  interpretador e caminho inexistente viram recusa com a mensagem do que
  fazer. O worker trata isso como erro de configuração, não defeito interno.
- `backend/arbites/api.py`: `PUT /targets` valida antes de gravar
  (`bad_python_path`, 422) — a recusa passa a acontecer ao configurar.
- `runner._mark_pending`: o aborto é registrado na execution SEMPRE, não só
  quando havia resultado para marcar. Era este `if changed` que apagava o
  motivo inteiro de uma execution sem CT vinculado.
- `backend/arbites/indexer.py`: coluna `abort_reason` (com migração
  tolerante), lida do bloco `aborted` da execution.
- `frontend/src/components/Automation.tsx`: a lista mostra "não executou" com
  o motivo na linha, em vez de "sem resultados".

## Scope boundaries

- Rodar um `.feature` sem nenhum CT espelho continua permitido: vínculo é
  rastreabilidade, não pré-requisito para executar (decisão da change 0067).
  O defeito nunca foi a execution sem CT — foi ela não contar o que houve.
- O `.env` do projeto-alvo continua sendo lido sozinho pelo `build_run_env`;
  nada aqui muda esse caminho.

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
- [x] Reproduzido o arranque do subprocess com o valor relatado
      (`...\\pf-b3-investidor-b3i-testes-front\\.env`): `PermissionError`,
      que é como a execution nascia vazia.

## Open questions

Nenhuma.
