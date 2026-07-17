# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

Exclusão de execution ([unverified] até implementar):

### Ubiquitous
- The system shall expor `DELETE /executions/{exec_id}` que move a pasta
  inteira da execution (JSON + evidências) para a lixeira e a remove do
  índice.

### Unwanted-behavior (must-not)
- The system shall not deletar uma execution com run ativo no runner (409).
- The system shall not apagar do disco — sempre lixeira.

### Acceptance criteria (a acrescentar)
- [unverified] DELETE move a pasta para a lixeira, some da listagem/índice
  e run ativo é recusado com 409 — verified by teste de API.
