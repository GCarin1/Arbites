# Change 0092-spec-coverage-criterio-ears-vinculado-a-ct-no — spec coverage: criterio EARS vinculado a CT no auditor

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** audit, requirements, testcases

## Why

Cobertura story↔CT é grossa: uma story com 6 critérios e 1 CT aparece
"coberta". O nível que transforma o Arbites em validador de especificação é
critério↔CT. Depende da 0091 (critérios parseáveis).

## What

- CT ganha frontmatter opcional `criteria: [EARS-1, ...]` (indexado),
  editável na UI do CT (picker dos critérios da story vinculada).
- Auditor ganha categoria `spec`: story com critério sem CT vinculado
  (warn), CT ready/automated de story com critérios sem `criteria` (info).
- Matriz/aba Requisitos: contagem "X/Y critérios cobertos" por story.

## Scope boundaries

- Depende da 0091 landada (tabela `criteria`).
- Vínculo é manual/assistido na v1 (a geração automática com vínculo é a
  0093).
- Stories sem seção de critérios ficam fora (mesmo opt-in da 0091).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Achados `spec` no auditor (critério sem CT; CT sem criteria); contagem X/Y por story — `backend/tests/test_audit.py` + `test_metrics.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
