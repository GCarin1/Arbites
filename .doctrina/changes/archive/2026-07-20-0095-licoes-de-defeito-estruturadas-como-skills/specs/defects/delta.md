# Delta — defects (change 0095)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall aceitar no defeito os campos opcionais de lição
  estruturada `lesson_when` / `lesson_procedure` / `lesson_antipattern`
  (frontmatter indexado, form na UI quando há root_cause, sugestão de IA
  opcional em preview), e as injeções de lição em prompts de IA shall
  preferir os campos estruturados quando presentes. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] Lição estruturada persiste e é preferida na injeção —
  verified by `backend/tests/test_lessons_learned.py`.
