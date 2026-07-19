# Change 0095-licoes-de-defeito-estruturadas-como-skills — licoes de defeito estruturadas como skills

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** defects

## Why

root_cause/fix/prevention são texto solto. Estruturar a lição (quando se
aplica / como evitar / anti-padrão) melhora a injeção nas gerações de IA e
alimenta o Pacote de Agente (0094) com skills de verdade.

## What

- Campos opcionais no defeito: `lesson_when`, `lesson_procedure`,
  `lesson_antipattern` (frontmatter, indexados).
- UI do defeito: quando root_cause é preenchido, seção "Estruturar lição"
  (form dos 3 campos) com sugestão da IA opcional (preview).
- `find_relevant_lessons` e o recap injetado passam a preferir os campos
  estruturados quando presentes (fallback: root_cause/fix).

## Scope boundaries

- Não cria pasta `lessons/` separada — a lição vive no defeito (fonte
  única, ADR 0001).
- Estruturar é opcional; lições soltas continuam válidas.

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Campos persistem/indexam; injeção usa os estruturados quando presentes — `backend/tests/test_lessons_learned.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
