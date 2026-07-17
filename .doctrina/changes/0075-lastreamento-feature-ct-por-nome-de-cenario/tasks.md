# Tasks — Change 0075-lastreamento-feature-ct-por-nome-de-cenario

- [ ] Backend: automation.feature_path/scenario_name no modelo do CT + indexer.
- [ ] Backend: scan por nome (gherkin_scan/scenarios) + GET /automation/sync-status.
- [ ] Backend: POST /automation/link-features (cria CTs verbatim) + acoes update/re-vincular.
- [ ] Testes de API: link, sync apos edicao do .feature (novo/modificado/renomeado).
- [ ] Frontend: modal de sync no Buscar .feature (selecao por item + acao).
- [ ] Build + smoke real com repo sintetico.
- [ ] Specs local-automation + testcases: EARS + criterios; bump minor.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
