# Spec — defects

**Capability:** defects
**Status:** active
**Implementation:** verified — M1 (CRUD/vínculo) + M1.5 (matriz) + M9 (aging/report; backend/arbites/metrics.py, backend/arbites/indexer.py)
**Realizes:** SC2
**Last updated:** 2026-07-10
**Version:** 0.6.0

## Purpose

Fecha a ponta da cadeia de rastreabilidade (… → Evidência → Defeito) sem
construir um bug tracker completo. Defeito na v1 é um `.md` em `defects/`
com metadados mínimos; o bug "de verdade" vive no sistema corporativo e
`external_key` aponta para ele.

## Requirements (EARS)

### Ubiquitous

- The system shall representar defeito como `.md` em `defects/` com
  frontmatter `id`, `title`, `status (open|fixed|closed)`, `severity`,
  `testcase`, `execution`, `external_key`, `opened` (data de abertura).
- The system shall expor `GET /defects`, `GET /defects/{id}` (com corpo),
  `POST /defects`, `PUT /defects/{id}`, `DELETE /defects/{id}` (lixeira).
- The system shall expor uma página dedicada de gerenciamento de defeitos
  (aba "Defeitos") com listagem, filtro por status e severidade, criação
  avulsa (sem exigir CT/execução), edição e exclusão — não apenas criação a
  partir de um resultado `failed` numa execução.
- The system shall permitir vincular defeitos a um resultado de execution
  (`results[].defects[]`).
- The system shall expor `POST /executions/{exec_id}/results/{ct_id}/defects`
  (vincular um defeito já existente, por id) e
  `DELETE /executions/{exec_id}/results/{ct_id}/defects/{defect_id}`
  (desvincular), além do vínculo automático ao criar defeito a partir de um
  resultado `failed`.

### Event-driven

- When um defeito é criado a partir de um resultado `failed`, the system
  shall preencher automaticamente `testcase` e `execution` no frontmatter.
- When o usuário navega por uma menção/link `@DF-XXXX`, the system shall
  abrir a aba Defeitos com o editor daquele defeito já aberto.

### State-driven

- While um defeito está `open`, the system shall exibi-lo na matriz de
  rastreabilidade na linha da story correspondente (ver `reporting`).

### Unwanted-behavior (must-not)

- The system shall not tentar ser um bug tracker completo (sem workflow de
  triagem, atribuição, comentários); é ponteiro + metadados.
- The system shall not aceitar vincular um `defect_id` inexistente (404) nem
  vincular/desvincular numa execution `closed` (409).

### Optional

- Where `external_key` está preenchida, the system may exibi-la como
  referência ao sistema corporativo.

## Acceptance criteria

1. [verified] Criar defeito a partir de um resultado failed vincula
   `testcase` e `execution` — verified by `backend/tests/test_defects.py`.
2. [verified] Defeito aparece na matriz de rastreabilidade da story —
   verified by `backend/tests/test_reporting_e2e.py`.
3. [verified] Defeito é carimbado com `opened` na criação e o report expõe
   sua idade (dias em aberto), severidade e squad do CT vinculado —
   verified by `backend/tests/test_defects.py`.

4. [verified] Vincular um defeito pré-existente a um resultado, vincular de
   novo (idempotente, sem duplicar) e desvincular funcionam via API dedicada;
   `defect_id` inexistente e execution fechada são rejeitados — verified by
   `backend/tests/test_executions.py`.

5. [verified] `GET /defects/{id}` devolve o defeito com corpo; `DELETE
   /defects/{id}` move para a lixeira e o defeito some da listagem e do
   individual (404) — verified by `backend/tests/test_defects.py`.

## Maturity

**MVP (committed):**

- CRUD mínimo, vínculo com resultado/execution, listagem na UI, página
  dedicada de gerenciamento (criar/editar/excluir avulso).

**Future (aspirational, not committed):**

- Export de resultados/defeitos como comentário no card do Businessmap
  (M6).

## Out of scope for this spec

- Workflow completo de bugs (fora de escopo da v1, explícito no intake).
