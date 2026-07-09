# Spec — testcases

**Capability:** testcases
**Status:** active
**Implementation:** verified — M0 + repositório BDD (backend/arbites/api.py, backend/arbites/parser.py, frontend TcRepository.tsx/TestCaseEditor.tsx)
**Realizes:** SC1
**Last updated:** 2026-07-09
**Version:** 0.4.0

## Purpose

Gerencia test cases (CTs) como arquivos Markdown com frontmatter em
`testcases/`, organizados em subpastas livres espelhadas pela UI. Um CT é
um documento com ciclo de vida próprio (`draft → ready → deprecated`),
distinto do resultado de execução, e pode ser `manual`, `automated` ou
`hybrid` — neste último caso vinculado a um cenário Gherkin por tag
`@CT-XXXX`.

## Requirements (EARS)

### Ubiquitous

- The system shall representar CT como `.md` com frontmatter `id`,
  `title`, `type (manual|automated|hybrid)`,
  `priority (critical|high|medium|low)`, `status (draft|ready|deprecated)`,
  `tags`, `story`, `automation {target, scenario_tag}` (apenas se
  `type != manual`), `created`, `updated`.
- The system shall tratar os headings `## Passos` e `## Resultado
  esperado` como âncoras obrigatórias para casos `manual` e `hybrid`
  (ausência = warning no reindex), e `## Objetivo` / `## Pré-condições`
  como recomendados.
- The system shall interpretar a lista ordenada sob `## Passos` como os
  steps marcáveis da execução manual.
- The system shall expor CRUD via `GET/POST /testcases`,
  `GET/PUT/DELETE /testcases/{id}` com filtros
  `story, status, tag, type, folder, q`, além de `GET /tree` para a árvore
  de pastas.
- The system shall expor o markdown cru via `GET/PUT /testcases/{id}/raw`
  para edição direta do arquivo.
- The system shall exigir `story` no frontmatter para o CT entrar na
  matriz de cobertura.
- The system shall aceitar corpo de CT em formato BDD (Feature/Scenario +
  Given/When/Then, EN ou PT-BR), extraindo os steps do CT das linhas
  Gherkin; este é o formato padrão de novos CTs (o markdown legado com
  `## Passos` permanece aceito).
- The system shall permitir criar e excluir pastas (aninhamento ilimitado)
  sob `testcases/` e mover um CT entre pastas
  (`POST /testcases/{id}/move`), preservando o ID; exclusão de pasta move
  o conteúdo para a lixeira.
- The system shall indexar e expor a data de criação (`created`) do CT na
  árvore e no detalhe.
- The system shall aceitar `external_key` opcional no frontmatter do CT
  (chave no sistema externo de origem) e indexá-la para detecção de
  duplicidade na migração (spec `xray-migration`).

### Event-driven

- When um CT é criado via API, the system shall gravá-lo na pasta de
  destino informada no body.
- When um CT `automated` ou `hybrid` referencia tag sem cenário
  correspondente, the system shall registrar warning "automação quebrada"
  no reindex (ver `indexing`).

### State-driven

- While um CT é `automated` puro, the system shall aceitar corpo mínimo
  (apenas objetivo); os steps reais vivem no `.feature`.

### Unwanted-behavior (must-not)

- The system shall not derivar o ID do nome do arquivo; rename/move não
  quebra vínculos.
- The system shall not escrever no repositório de automação (feature
  files são read-only para o Arbites).
- The system shall not emitir warning de heading ausente para corpo BDD
  válido (Scenario + steps Gherkin).
- The system shall not aceitar caminhos de pasta fora de `testcases/`
  (path traversal → 422).

### Optional

- Where o usuário edita o CT no Obsidian ou editor externo, the system may
  refletir a mudança na UI em segundos via reindex incremental.

## Acceptance criteria

1. [verified] Criar CT pela UI grava `.md` no folder escolhido com
   frontmatter completo — verified by `backend/tests/test_testcases.py`.
2. [verified] Editar o `.md` externamente atualiza a UI sem ação manual
   — verified by `backend/tests/test_indexing.py`.
3. [verified] CT manual sem `## Passos` gera warning, não erro —
   verified by `backend/tests/test_testcases.py`.
4. [verified] `GET /tree` espelha a árvore real de `testcases/` —
   verified by `backend/tests/test_testcases.py`.
5. [verified] Corpo BDD tem steps extraídos de Given/When/Then (usados no
   snapshot da execution) e não gera warning de heading — verified by
   `backend/tests/test_tc_repository.py`.
6. [verified] Criar pasta aninhada, mover CT (drag & drop) e excluir pasta
   (conteúdo → lixeira, fora do índice) — verified by
   `backend/tests/test_tc_repository.py`.
7. [verified] `created` indexado e presente na árvore/detalhe — verified by
   `backend/tests/test_tc_repository.py`.

## Maturity

**MVP (committed):**

- CRUD, repositório de pastas centralizado (criar/excluir/mover, drag &
  drop), formato BDD padrão, editor form + markdown cru, filtros, `created`.

**Future (aspirational, not committed):**

- Versionamento/diff de CT dentro da UI (hoje: git no workspace).

## Out of scope for this spec

- Resultados de execução (ver `executions`) — status de documento ≠
  status de resultado.
- Scan de features e vínculo por tag (ver `indexing`).
