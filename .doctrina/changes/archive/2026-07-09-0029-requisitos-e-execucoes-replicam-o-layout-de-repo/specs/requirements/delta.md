# Spec Delta — capability: requirements

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/requirements/spec.md`

---

## Context

Doc de ajustes §1.2: requisitos replicam o layout de repositório — hierarquia
epic→story centralizada no conteúdo, drag & drop de story entre epics
(reassocia o `epic`), detalhe por clique com Voltar, exclusão com confirmação
e **data de criação** registrada no frontmatter e exposta na listagem.

## Requirements (EARS) — deltas

### Ubiquitous (ADDED)

- The system shall carimbar `created` (data) no frontmatter do requisito na
  criação, indexá-lo e expô-lo na listagem/detalhe.

## Acceptance criteria (ADDED)

4. [verified] Requisito criado recebe `created` e a listagem o expõe —
   verified by `backend/tests/test_requirements.py`.
