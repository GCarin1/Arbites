# Spec — workspace-core

**Capability:** workspace-core
**Status:** active
**Implementation:** verified — M0 (backend/arbites/workspace.py, backend/arbites/api.py)
**Realizes:** SC1
**Last updated:** 2026-09-17
**Version:** 0.7.0

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
- The system shall expor a lixeira pela API: `GET /trash` (itens com origem,
  data e tipo), `POST /trash/{name}/restore` (devolve ao caminho de origem —
  ou à pasta do tipo quando a origem não foi registrada — sufixando em
  colisão, e reindexa o que voltou) e `DELETE /trash` (esvaziar). A UI
  oferece listar/restaurar/esvaziar na aba Problemas.
- The system shall gerar o arquivo de configuracao inicial comentado e cobrindo todos os blocos que o produto consulta, incluindo os opcionais, porque configuracao que nao aparece no arquivo e configuracao que ninguem descobre.
- The system shall declarar no proprio arquivo de configuracao que segredo nao entra nele e onde ele mora, ja que o arquivo fica dentro do workspace versionavel.
- The system shall incluir esse mesmo aviso na lista de problemas da API, para que a interface desatualizada — que continua consultando a API atual — possa mostrá-lo a quem não viu o terminal.
- The system shall informar, no arranque e na rota de saúde, qual código o processo está executando — ramo, commit, data do commit e se há alteração local não commitada —, para separar "o conserto não funcionou" de "o conserto não está rodando".

### Event-driven

- When um artefato é criado via UI/API, the system shall consumir o
  contador do prefixo correspondente em `counters.json` para atribuir o ID.
- When um artefato é deletado via API, the system shall movê-lo para
  `.arbites/trash/` em vez de apagar do disco, registrando um sidecar
  `<nome>.arbtrash` com o caminho de origem e a data de moção.
- When um arquivo criado à mão traz ID manual maior que o contador, the
  system shall ajustar o contador para `max(existente)+1` no reindex.
- When o processo sobe e o código do frontend é mais recente que o build servido, the system shall avisar no arranque que a interface entregue é a anterior, nomeando o comando de reconstrução com o caminho desta instalação.
- When uma exceção não prevista escapa de uma rota, the system shall responder um erro legível com identificador de rastreio e registrar o traceback completo no log sob o mesmo identificador.

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
- The system shall not tratar ausência de build como build velho, nem afirmar obsolescência quando o código-fonte não está ao lado do `dist`; sem o que comparar a resposta é "não sei", e a comparação por data de arquivo só justifica aviso, nunca recusa.
- The system shall not inventar identidade de código quando não há checkout ao lado; nesse caso declara a ausência, porque um identificador plausível e errado é pior que nenhum.
- The system shall not repassar na resposta o texto de uma exceção não prevista; ela pode carregar caminho de arquivo, trecho de consulta ou credencial, e essa resposta chega ao navegador.

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

5. [verified] Um CT deletado aparece em `GET /trash` com origem/data;
   restaurar devolve o arquivo ao caminho original e ao índice sem
   sobrescrever (sufixa em colisão); esvaziar limpa a lixeira — verified by
   `backend/tests/test_trash.py`.
6. [unverified] O arquivo gerado traz os onze blocos consultados pelo codigo, nasce comentado, avisa que segredo nao entra nele, carrega como a configuracao padrao e nao sobrescreve um arquivo existente — verified by `backend/tests/test_config_padrao.py`.
7. [verified] Build em dia não avisa; `dist` mais antigo que `src` avisa no arranque e na lista de problemas, com o comando e o caminho corretos; `index.html`, `package.json` e `vite.config.ts` contam como fonte e `node_modules` não; e `dist` sem código ao lado (o caso do container) não afirma nada — verified by `backend/tests/test_build_desatualizado.py`.
8. [verified] Em checkout git a identidade traz commit, ramo e o estado de alteração local; sem git, ou sem o binário do git, responde a ausência sem derrubar o processo; a rota de saúde devolve isso e continua aberta sem sessão — verified by `backend/tests/test_versao_em_execucao.py`.
9. [verified] Uma rota real que levanta exceção responde 500 com código `internal_error` e identificador próprio a cada falha, sem traceback nem o texto da exceção no corpo; o traceback e o texto vão para o log sob o mesmo identificador; e os erros já previstos continuam com a mensagem deles — verified by `backend/tests/test_falha_inesperada.py`.

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
