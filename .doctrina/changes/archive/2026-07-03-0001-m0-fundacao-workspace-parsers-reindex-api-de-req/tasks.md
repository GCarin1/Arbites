# Tasks — Change 0001-m0-fundacao-workspace-parsers-reindex-api-de-req

- [x] Backend: esqueleto do pacote `arbites` (config, resolução do
      workspace, bootstrap da estrutura, `requirements.txt`).
- [x] Backend: parser de frontmatter + headings com validações
      (warnings, não erros).
- [x] Backend: indexer SQLite — esquema, `reindex_full`, `reindex_file`,
      warnings de integridade, ajuste de contadores.
- [x] Backend: watcher (watchdog) chamando `reindex_file`.
- [x] Backend: API M0 — `/workspace`, `/workspace/reindex`, `/warnings`,
      `/tree`, CRUD `/requirements`, CRUD `/testcases` + `/raw`,
      DELETE → trash, estáticos da SPA.
- [x] Backend: testes pytest cobrindo os critérios de aceite de
      workspace-core, indexing (menos Gherkin), requirements e testcases.
- [x] Frontend: scaffold Vite + React + TS com tokens do design system.
- [x] Frontend: árvore de testcases + lista de requisitos (sidebar).
- [x] Frontend: editor de CT (form + aba markdown cru) e editor de
      requisito.
- [x] Frontend: tela Problemas (warnings) e botão de reindex.
- [x] README.md com passo a passo de instalação e execução.
- [x] Deltas das 4 specs afetadas (Implementation + evidências reais).
- [x] `doctrina analyze` limpo e `doctrina verify` verde.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-03-0001-m0-fundacao-workspace-parsers-reindex-api-de-req/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
