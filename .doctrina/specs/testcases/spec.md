# Spec — testcases

**Capability:** testcases
**Status:** active
**Implementation:** verified — M0 + repositório BDD (backend/arbites/api.py, backend/arbites/parser.py, frontend TcRepository.tsx/TestCaseEditor.tsx)
**Realizes:** SC1
**Last updated:** 2026-07-21
**Version:** 0.9.0

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
  `GET/PUT/DELETE /testcases/{id}` com filtros combináveis
  `story, status, tag, type, priority, folder, squad, q`, além de
  `GET /tree` para a árvore de pastas.
- The system shall oferecer no repositório de CTs uma busca fixa no topo e
  filtros combinados (status/prioridade/tipo/tag) que usam o MESMO endpoint
  `GET /testcases` do servidor — a árvore exibe apenas os itens que
  casaram, com a contagem por pasta mostrando `casaram/total` e pastas sem
  match ocultas.
- The system shall abrir um painel lateral de detalhes ao selecionar um CT
  na árvore (status, tipo, prioridade, story, squad, tags e defeitos
  vinculados — via `GET /defects?testcase=`), com ações rápidas (mudar
  status, copiar ID, abrir o editor completo) sem sair da árvore; o editor
  completo abre por duplo clique ou pelo botão do painel.
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
- The system shall permitir mover uma pasta inteira (drag & drop) para dentro
  de outra pasta sob `testcases/` via `POST /testcases/folders/move`,
  preservando toda a subárvore e reindexando cada `.md` afetado no novo
  caminho (IDs preservados).
- The system shall indexar e expor a data de criação (`created`) do CT na
  árvore e no detalhe.
- The system shall aceitar `external_key` opcional no frontmatter do CT
  (chave no sistema externo de origem) e indexá-la para detecção de
  duplicidade na migração (spec `xray-migration`).

- The system shall expor `GET /testcases/{id}/results` (histórico de
  resultados do CT: execution, status, data, duração — mais recente
  primeiro, da tabela `results`), exibido no painel lateral do repositório
  e no editor ("já passou no passado?").
- The system shall aceitar em `automation` o par `feature_path` +
  `scenario_name` como vínculo alternativo à `scenario_tag` (lastreamento
  por nome de cenário; ver `local-automation`); `automation` exige tag OU
  nome (422 sem nenhum).
- The system shall aceitar `criteria: [EARS-n, ...]` no frontmatter do CT
  (vínculo aos critérios EARS da story, indexado em `tc_criteria` e exposto
  em `GET /testcases/{id}`), com picker na UI do CT restrito aos critérios
  da story vinculada; lista vazia limpa o vínculo (ver `requirements` para o
  parse dos critérios e `audit` para a cobertura de spec).
- The system shall aceitar `quarantine: bool` no frontmatter do CT (toggle
  na UI, indexado, exposto em `GET /testcases/{id}`); `false` não é gravado
  no YAML. O detalhe do CT shall exibir um badge de `flaky` quando o
  resultado alternou pass/fail nas últimas execuções (via `GET
  /metrics/flaky`) e um badge de `quarentena` quando o CT está isolado (ver
  `reporting` para o efeito no pass rate).

### Event-driven

- When um CT é criado via API, the system shall gravá-lo na pasta de
  destino informada no body.
- When um CT `automated` ou `hybrid` referencia tag sem cenário
  correspondente, the system shall registrar warning "automação quebrada"
  no reindex (ver `indexing`).
- When o usuário arrasta uma pasta que contém um ou mais casos de teste
  (recursivamente) para dentro de outra pasta, the system shall abrir um
  modal de confirmação informando quantos CTs serão movidos junto, e só
  mover após confirmação explícita.

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
- The system shall not aceitar mover uma pasta para dentro dela mesma ou de
  uma pasta descendente (422); nem sobrescrever uma pasta existente com o
  mesmo nome no destino (409).

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

8. [verified] Mover uma pasta com CTs para outra pasta preserva os IDs e
   atualiza os caminhos; mover para dentro de si mesma/descendente e para um
   destino já ocupado são rejeitados — verified by
   `backend/tests/test_tc_repository.py`.

9. [verified] O filtro `priority` combina com os demais
   (`status`/`q`/`tag`/`type`) em `GET /testcases`, e
   `GET /defects?testcase=` lista os defeitos vinculados a um CT (fonte do
   painel lateral) — verified by `backend/tests/test_testcases.py`.

10. [verified] O histórico de resultados por CT lista as execuções
    passadas em ordem (endpoint + painel/editor) — verified by
    `backend/tests/test_testcases.py` (`test_testcase_results_history`).
11. [verified] CT com `automation.scenario_name` é indexado, entra no scan
    do target e o run/coleta casa resultado por nome — verified by
    `backend/tests/test_feature_sync.py` e
    `backend/tests/test_local_runs.py`.
12. [verified] CT aceita `criteria: [EARS-n]`, indexa em `tc_criteria` e o
    expõe em `GET /testcases/{id}`; edição troca e lista vazia limpa; picker
    na UI restrito aos critérios da story — verified by
    `backend/tests/test_testcases.py`
    (`test_testcase_criteria_link_indexed_and_editable`) + build + revisão
    visual (`frontend/src/components/TestCaseEditor.tsx`).
13. [verified] O aceite de um CT gerado POR critério (ver `ai-assist`)
    persiste `story` + `criteria` no CT criado — verified by
    `backend/tests/test_ai_generate.py`
    (`test_generate_per_criterion_tags_and_accept_links`).

14. [verified] O toggle de quarentena persiste `quarantine: true` no
    frontmatter (e `false` remove a chave), indexa e volta como bool; o
    badge flaky aparece para CT com resultado alternante — verified by
    `backend/tests/test_testcases.py`
    (`test_quarantine_toggle_persists_in_frontmatter`) + build + revisão
    visual.

## Maturity

**MVP (committed):**

- CRUD, repositório de pastas centralizado (criar/excluir/mover pasta ou CT,
  drag & drop), formato BDD padrão, editor form + markdown cru, filtros
  combinados com busca fixa e contagem por pasta, painel lateral de detalhes
  com ações rápidas, `created`.

**Future (aspirational, not committed):**

- Versionamento/diff de CT dentro da UI (hoje: git no workspace).

## Out of scope for this spec

- Resultados de execução (ver `executions`) — status de documento ≠
  status de resultado.
- Scan de features e vínculo por tag (ver `indexing`).
