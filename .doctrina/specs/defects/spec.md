# Spec — defects

**Capability:** defects
**Status:** active
**Implementation:** planned — deferido ao M1 (após o walking skeleton M0)
**Realizes:** SC2
**Last updated:** 2026-07-03
**Version:** 0.1.0

## Purpose

Fecha a ponta da cadeia de rastreabilidade (… → Evidência → Defeito) sem
construir um bug tracker completo. Defeito na v1 é um `.md` em `defects/`
com metadados mínimos; o bug "de verdade" vive no sistema corporativo e
`external_key` aponta para ele.

## Requirements (EARS)

### Ubiquitous

- The system shall representar defeito como `.md` em `defects/` com
  frontmatter `id`, `title`, `status (open|fixed|closed)`, `severity`,
  `testcase`, `execution`, `external_key`.
- The system shall expor `GET /defects`, `POST /defects`,
  `PUT /defects/{id}`.
- The system shall permitir vincular defeitos a um resultado de execution
  (`results[].defects[]`).

### Event-driven

- When um defeito é criado a partir de um resultado `failed`, the system
  shall preencher automaticamente `testcase` e `execution` no frontmatter.

### State-driven

- While um defeito está `open`, the system shall exibi-lo na matriz de
  rastreabilidade na linha da story correspondente (ver `reporting`).

### Unwanted-behavior (must-not)

- The system shall not tentar ser um bug tracker completo (sem workflow de
  triagem, atribuição, comentários); é ponteiro + metadados.

### Optional

- Where `external_key` está preenchida, the system may exibi-la como
  referência ao sistema corporativo.

## Acceptance criteria

1. [unverified] Criar defeito a partir de um resultado failed vincula
   `testcase` e `execution` — verified by `tests/test_defects.py`.
2. [unverified] Defeito aparece na matriz de rastreabilidade da story —
   verified by `tests/test_defects.py`.

## Maturity

**MVP (committed):**

- CRUD mínimo, vínculo com resultado/execution, listagem na UI.

**Future (aspirational, not committed):**

- Export de resultados/defeitos como comentário no card do Businessmap
  (M6).

## Out of scope for this spec

- Workflow completo de bugs (fora de escopo da v1, explícito no intake).
