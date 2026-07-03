# Spec — workspace-core

**Capability:** workspace-core
**Status:** active
**Implementation:** verified — M0 (backend/arbites/workspace.py, backend/arbites/api.py)
**Realizes:** SC1
**Last updated:** 2026-07-03
**Version:** 0.2.0

## Purpose

Define e gerencia o workspace em filesystem — a fonte de verdade do
Arbites. Cobre a estrutura de pastas (`requirements/`, `testcases/`,
`executions/`, `defects/`, `.arbites/`), a configuração `arbites.yaml`, os
contadores de ID sequenciais e a regra de que tudo que existe na interface
existe no disco em formatos abertos (Markdown, YAML, JSON, Gherkin).

## Requirements (EARS)

### Ubiquitous

- The system shall usar o filesystem como única fonte de verdade; o banco
  SQLite em `.arbites/index.db` é índice descartável e reconstruível.
- The system shall persistir todos os artefatos em formatos abertos:
  requisitos e test cases como Markdown com frontmatter YAML, executions
  como JSON, configuração como YAML.
- The system shall ler a configuração do workspace de `arbites.yaml` na
  raiz (nome, prefixos de ID por tipo, automation targets, providers IA).
- The system shall manter os próximos IDs sequenciais por prefixo em
  `.arbites/counters.json`.
- The system shall tratar o nome de arquivo como livre e sem semântica; o
  ID canônico vive no frontmatter do artefato.
- The system shall particionar `executions/` por ano.
- The system shall gerar arquivos `.md` legíveis e editáveis no Obsidian
  sem conversão.
- The system shall servir a API em `http://localhost:8347` a partir de um
  processo único (uvicorn), servindo o frontend buildado como estático.

### Event-driven

- When um artefato é criado via UI/API, the system shall consumir o
  contador do prefixo correspondente em `counters.json` para atribuir o ID.
- When um artefato é deletado via API, the system shall movê-lo para
  `.arbites/trash/` em vez de apagar do disco.
- When um arquivo criado à mão traz ID manual maior que o contador, the
  system shall ajustar o contador para `max(existente)+1` no reindex.

### State-driven

- While nenhum provider de IA está configurado, the system shall manter
  100% das funções centrais operacionais (IA é opcional).

### Unwanted-behavior (must-not)

- The system shall not depender de nuvem para qualquer função central
  (local-first / offline-first).
- The system shall not impor estrutura às subpastas de `testcases/`; o
  usuário organiza como quiser e a UI espelha a árvore real.
- The system shall not gravar segredos (PAT GitHub, chaves de IA) em
  arquivos do workspace; segredos vivem no keyring do SO.

### Optional

- Where o workspace é versionado em git, the system may recomendar incluir
  `.arbites/` inteiro no `.gitignore`.

## Acceptance criteria

1. [verified] `GET /workspace` retorna a config do `arbites.yaml` e o
   status do índice — verified by `backend/tests/test_workspace.py`.
2. [verified] Apagar `index.db` e reindexar reconstrói o índice sem
   perda de dados — verified by `backend/tests/test_workspace.py`.
3. [verified] Criar um CT via API consome o contador e grava `.md` com
   ID no frontmatter — verified by `backend/tests/test_workspace.py`.
4. [verified] DELETE move o arquivo para `.arbites/trash/` e ele é
   removido do índice — verified by `backend/tests/test_workspace.py`.

## Maturity

**MVP (committed):**

- Estrutura de workspace, `arbites.yaml`, contadores, trash, processo
  único servindo API + estáticos.

**Future (aspirational, not committed):**

- Múltiplos workspaces simultâneos; troca de workspace pela UI.

## Out of scope for this spec

- Parsing e indexação (ver `indexing`).
- CRUD das entidades (ver `requirements`, `testcases`, `executions`,
  `defects`).
