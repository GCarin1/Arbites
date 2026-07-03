# Spec — requirements

**Capability:** requirements
**Status:** active
**Implementation:** planned — bootstrap pré-código; entra no walking skeleton (M0)
**Realizes:** SC1
**Last updated:** 2026-07-03
**Version:** 0.1.0

## Purpose

Gerencia requisitos locais — Epics e Stories — como arquivos Markdown com
frontmatter em `requirements/`. A story local é um espelho resumido do
detalhe que vive no Confluence (colagem manual na v1), com `external_key`
apontando para o sistema corporativo (Jira hoje, Businessmap depois).

## Requirements (EARS)

### Ubiquitous

- The system shall representar Epic como `.md` com frontmatter `id`,
  `kind: epic`, `title`, `status (active|done|cancelled)`, `external_key`,
  `tags`.
- The system shall representar Story como `.md` com frontmatter `id`,
  `kind: story`, `title`, `epic`, `status`, `external_key`,
  `confluence_url` (opcional), `tags`.
- The system shall expor CRUD via `GET/POST /requirements`,
  `GET/PUT/DELETE /requirements/{id}`, com filtros `kind` e `status`.
- The system shall suportar critérios de aceite em formato EARS no corpo
  da story (insumo para geração de CTs por IA no M5).

### Event-driven

- When uma story referencia um epic inexistente, the system shall
  registrar warning de integridade no reindex (ver `indexing`).
- When um requisito é deletado, the system shall movê-lo para
  `.arbites/trash/`.

### State-driven

- While uma story está `active`, the system shall contabilizá-la no
  denominador da cobertura de requisito (ver `reporting`).

### Unwanted-behavior (must-not)

- The system shall not sincronizar automaticamente com Confluence ou Jira;
  `external_key` e `confluence_url` são referências textuais manuais.

### Optional

- Where `confluence_url` está preenchida, the system may exibir link
  clicável para o detalhe completo da story.

## Acceptance criteria

1. [unverified] Criar epic e story pela API gera `.md` válidos em
   `requirements/` com IDs sequenciais — verified by
   `tests/test_requirements.py`.
2. [unverified] `GET /requirements?kind=story&status=active` filtra
   corretamente — verified by `tests/test_requirements.py`.
3. [unverified] Story com `epic` inexistente aparece em `/warnings` —
   verified by `tests/test_requirements.py`.

## Maturity

**MVP (committed):**

- CRUD de epic/story, vínculo story→epic, tela de lista/editor na UI.

**Future (aspirational, not committed):**

- Import read-only de cards do Businessmap como requisitos locais (M6).

## Out of scope for this spec

- Matriz de cobertura e métricas (ver `reporting`).
- Test cases (ver `testcases`).
