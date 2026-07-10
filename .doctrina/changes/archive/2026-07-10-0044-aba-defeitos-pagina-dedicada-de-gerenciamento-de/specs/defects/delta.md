# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

## Requirements (EARS)

### Ubiquitous

- The system shall expor uma página dedicada de gerenciamento de defeitos
  (aba "Defeitos") com listagem, filtro por status e severidade, criação
  avulsa (sem exigir CT/execução), edição e exclusão — não apenas criação a
  partir de um resultado `failed` numa execução.
- The system shall expor `GET /defects/{id}` (defeito individual, incluindo
  o corpo/descrição) e `DELETE /defects/{id}` (move para a lixeira).

### Event-driven

- When o usuário navega por uma menção/link `@DF-XXXX`, the system shall
  abrir a aba Defeitos com o editor daquele defeito já aberto.

## Acceptance criteria

5. [verified] `GET /defects/{id}` devolve o defeito com corpo; `DELETE
   /defects/{id}` move para a lixeira e o defeito some da listagem e do
   individual (404) — verified by `backend/tests/test_defects.py`.
