# Spec — indexing

**Capability:** indexing
**Status:** active
**Implementation:** verified — M0 (parsers/reindex) + M3 (scan Gherkin: backend/arbites/gherkin_scan.py)
**Realizes:** SC1, SC8
**Last updated:** 2026-07-04
**Version:** 0.3.0

## Purpose

Transforma o filesystem em um índice SQLite consultável e descartável.
Cobre os parsers (frontmatter Markdown via `python-frontmatter` +
`markdown-it-py`, Gherkin via pacote oficial `gherkin`), o reindex completo
e incremental (watchdog), as validações de integridade (tabela `warnings`)
e o mapa de cenários automatizados `@CT-XXXX → (feature, cenário, linha)`.

## Requirements (EARS)

### Ubiquitous

- The system shall manter em SQLite as tabelas `requirements`, `testcases`,
  `tc_tags`, `scenarios`, `executions`, `results`, `evidences`, `defects` e
  `warnings`, conforme o esquema do documento de intake (§7).
- The system shall oferecer reindex completo via CLI (`arbites reindex`) e
  via botão na UI (`POST /workspace/reindex`).
- The system shall completar o reindex completo em menos de 5 segundos
  para um workspace com 2.000 test cases.
- The system shall parsear feature files com o pacote oficial `gherkin`,
  resolvendo `# language:` nativamente e normalizando os steps para
  `keyword_type: given|when|then` independente do idioma.
- The system shall, no reindex, escanear o `features_glob` de cada target
  e montar o mapa `@CT-XXXX → (feature_file, scenario_name, line)`.
- The system shall expor os warnings de integridade via `GET /warnings` e
  em uma tela "Problemas" na UI.

### Event-driven

- When um arquivo do workspace muda no disco (watchdog), the system shall
  reparsear apenas o arquivo alterado e atualizar o índice em segundos.
- When o reindex encontra frontmatter inválido, story inexistente
  referenciada, tag órfã ou heading obrigatório ausente, the system shall
  registrar um warning em `warnings` sem bloquear o reindex.
- When o reindex encontra ID duplicado, the system shall marcar ambos os
  arquivos como conflito (erro, não warning).
- When o reindex encontra tag `@CT-XXXX` sem CT correspondente, the system
  shall registrar warning "cenário órfão".
- When o reindex encontra CT `automated`/`hybrid` sem tag no repo de
  automação, the system shall registrar warning "automação quebrada".
- When o reindex encontra a mesma tag `@CT-XXXX` em dois cenários, the
  system shall registrar erro de tag duplicada.

### State-driven

- While casos `manual` ou `hybrid` não possuem os headings `## Passos` e
  `## Resultado esperado`, the system shall emitir warning (não erro) no
  reindex.

### Unwanted-behavior (must-not)

- The system shall not ignorar silenciosamente arquivos inválidos; todo
  problema aparece na tela de warnings.
- The system shall not armazenar o conteúdo binário de evidências no
  índice; apenas caminho relativo, hash SHA-256, MIME e timestamp.

### Optional

- Where o índice está ausente ou corrompido, the system may reconstruí-lo
  integralmente do filesystem sem intervenção além do comando de reindex.

## Acceptance criteria

1. [verified] Editar um CT em editor externo reflete na API/UI em
   segundos sem ação manual — verified by `backend/tests/test_indexing.py`.
2. [verified] Reindex de workspace com 2.000 CTs conclui em < 5 s —
   verified by `backend/tests/test_indexing_perf.py`.
3. [verified] ID duplicado gera conflito listado em `/warnings` —
   verified by `backend/tests/test_indexing.py`.
4. [verified] Feature em `# language: pt` é parseada e mapeada por tag
   `@CT-XXXX` — verified by `backend/tests/test_gherkin.py`.

## Maturity

**MVP (committed):**

- Reindex completo + incremental, warnings de integridade, scan de
  features por target, contadores ajustados no reindex.

**Future (aspirational, not committed):**

- Busca full-text no índice; cache de AST de markdown.

## Out of scope for this spec

- Estrutura do workspace (ver `workspace-core`).
- Execução dos cenários automatizados (ver `local-automation`,
  `ci-automation`).
