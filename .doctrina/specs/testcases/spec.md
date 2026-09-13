# Spec — testcases

**Capability:** testcases
**Status:** active
**Implementation:** verified — M0 + repositório BDD (backend/arbites/api.py, backend/arbites/parser.py, frontend TcRepository.tsx/TestCaseEditor.tsx)
**Realizes:** SC1
**Last updated:** 2026-09-13
**Version:** 0.13.0

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
- The system shall oferecer no repositório de CTs um modo de seleção
  múltipla com ações em lote (mudar status, mover de pasta, excluir para a
  lixeira), executadas pelo cliente sobre os endpoints unitários, com
  confirmação prévia (`ConfirmModal`) e resumo de sucesso/falha (toast
  `X ok · Y falha(s)`); a lista de executions oferece exclusão em lote no
  mesmo padrão (ver `executions`). Sem endpoint bulk no backend (N chamadas).
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
- The system shall indexar `needs_rerun` do frontmatter do CT (bool exposto
  em `GET /testcases/{id}`), aceitar o filtro `needs_rerun` em `GET
  /testcases` e exibir o badge "precisa re-execução" no repositório e no
  detalhe do CT (o flag é gerido pela sync de features — ver
  `local-automation`).
- The system shall manter o workspace como repositório git, criando-o com `git init` e um `.gitignore` do índice descartável na primeira escrita quando ainda não existir `.git/`.
- The system shall gravar um commit por AÇÃO semântica da interface — criar, editar, mover e excluir um caso de teste —, com mensagem descrevendo a ação e autor vindo da sessão, nunca um commit por gravação de arquivo.
- The system shall expor `GET /testcases/{id}/versions` (histórico do arquivo), `GET /testcases/{id}/versions/{sha}` (o conteúdo naquele commit), `GET /testcases/{id}/versions/diff?a=&b=` (comparação unificada) e `POST /testcases/{id}/versions/{sha}/restore` (restauração).
- The system shall apresentar o histórico numa aba do próprio caso de teste, com a versão escolhida comparável à atual e restaurável dali.
- The system shall serializar as operações de git do workspace numa fila única por processo, para que duas escritas simultâneas esperem em vez de disputar o lock do repositório.
- The system shall executar as operações de git fora do laço de eventos, como já faz com as demais chamadas bloqueantes.

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
- When um arquivo do workspace é alterado por fora da interface e existe alteração não commitada, the system shall registrá-la como commit de autoria externa antes de responder o histórico, para que a edição no Obsidian não suma do registro.
- When uma versão anterior é restaurada, the system shall gravar a restauração como um commit NOVO, preservando o histórico em vez de reescrevê-lo.
- When um commit de versionamento não acontece por falha do git, the system shall registrar um aviso no log identificando a ação e o motivo, em vez de seguir em silêncio.

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
- The system shall not versionar o índice descartável, a lixeira nem os segredos do workspace; o que o `.gitignore` cobre não entra em commit nenhum.
- The system shall not falhar uma operação de caso de teste porque o git falhou ou não está instalado; o versionamento é registro, e registro que derruba a escrita do usuário é pior do que registro nenhum.

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

15. [verified] `needs_rerun` é indexado e exposto como bool; o filtro
    `GET /testcases?needs_rerun=true` lista só os marcados; badge no
    repositório e no detalhe — verified by `backend/tests/test_testcases.py`
    (`test_needs_rerun_filter_lists_only_flagged`) + build + revisão visual.

16. [verified] Seleção múltipla no repositório aplica status/mover/excluir
    em lote com confirmação e resumo X ok · Y falhas; executions têm
    exclusão em lote no mesmo padrão — verified by build + revisão visual
    (os endpoints unitários já são cobertos por
    `backend/tests/test_testcases.py` e `backend/tests/test_executions.py`).
17. [verified] Criar, editar e mover um caso de teste gera um commit por ação, com a mensagem da ação e o e-mail da sessão como autor, e o índice descartável fica fora do repositório — verified by `backend/tests/test_versioning.py`.
18. [verified] O histórico de um caso lista suas versões, a comparação entre duas mostra a linha alterada e restaurar uma versão anterior devolve o conteúdo gravando um commit novo — verified by `backend/tests/test_versioning.py`.
19. [verified] Uma edição feita por fora da interface entra no histórico como commit de autoria externa, e um workspace onde o git não funciona continua aceitando criar e editar casos — verified by `backend/tests/test_versioning.py`.
20. [verified] Doze gravações simultâneas geram doze commits e não deixam nenhum arquivo fora do histórico — verified by `backend/tests/test_versioning.py`.
21. [verified] Um commit impedido por falha do git deixa aviso no log com a ação que se perdeu, e a operação do usuário continua respondendo normalmente — verified by `backend/tests/test_versioning.py`.

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
