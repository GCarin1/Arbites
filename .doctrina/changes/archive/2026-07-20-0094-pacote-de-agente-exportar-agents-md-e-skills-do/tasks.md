# Tasks — Change 0094-pacote-de-agente-exportar-agents-md-e-skills-do

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Backend `agent_pack.py`: renderers AGENTS.md/skills/specs sobre dados existentes.
- [x] Rota `GET /agent-pack` (zipfile + StreamingResponse; layouts).
- [x] UI: seção Pacote de Agente na sub-aba Context Pack (escopo + layout + zip).
- [x] Testes `test_agent_pack.py` + `npm run build`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0094-pacote-de-agente-exportar-agents-md-e-skills-do/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
