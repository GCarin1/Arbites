# Spec Delta — capability: project-memory

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/project-memory/spec.md`

---

Tipos novos na timeline ([unverified] até implementar):

### Ubiquitous
- The system shall incluir na timeline os tipos `testcase` (criação de CT,
  de `testcases.created`) e `result` (mudança de resultado em execution,
  de `result_events` — "CT-X passou/falhou em EXEC-Y"), ambos filtráveis.

### Unwanted-behavior (must-not)
- The system shall not afogar a timeline: o tipo `result` vem DESLIGADO por
  default no filtro da UI (opt-in), respeitando o limite global.

### Acceptance criteria (a acrescentar)
- [unverified] Criar um CT gera evento `testcase`; marcar resultado numa
  execution gera evento `result` (com o filtro ligado); default não mostra
  `result` — verified by `backend/tests/test_project_memory.py`.
