# Spec Delta — capability: defects

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/defects/spec.md`

---

## Context

M9 dá aging aos defeitos: o frontmatter ganha `opened` (data de abertura,
carimbada na criação), indexado como `opened_at`. O squad do defeito é o
squad efetivo do CT vinculado. Isto alimenta o painel de defeitos do
dashboard (ver delta de `reporting`).

## Requirements (EARS) — deltas

### Ubiquitous (MODIFIED)

- The system shall representar defeito como `.md` em `defects/` com
  frontmatter `id`, `title`, `status (open|fixed|closed)`, `severity`,
  `testcase`, `execution`, `external_key`, `opened` (data de abertura).

## Acceptance criteria (ADDED)

3. [verified] Defeito é carimbado com `opened` na criação e o report expõe
   sua idade (dias em aberto), severidade e squad do CT vinculado —
   verified by `backend/tests/test_defects.py`.
