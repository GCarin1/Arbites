# Tasks — Change 0043

- [x] Backend: `gherkin_scan.list_feature_files` (scan avulso, sem tocar no índice/DB).
- [x] Backend: `AutomationTargetIn`/`AutomationTargetsIn`; `PUT /targets` (full-replace + reindex).
- [x] Backend: `GET /automation/browse-features` (scan de local_path arbitrário, 422 se não existir).
- [x] Backend: `GET /targets` (list_targets) passa a incluir python_path/working_dir/timeout_minutes.
- [x] Frontend: `TargetsCard` — tabela editável + form (nome, caminho, python, working dir, timeout,
      features_glob avançado) + botão "Buscar arquivos .feature" com lista clicável (restringe a um
      arquivo) + "Salvar configuração" (PUT /targets).
- [x] Testes backend (persist, full-replace, local_path ausente não crasha, browse com contagem,
      glob default, path inválido 422, restringir a 1 arquivo) + suíte verde + build.
- [x] Smoke HTTP contra servidor real (browse → save → list) confirmando o fluxo ponta a ponta.

## Closing steps

- [x] Apply: merge delta na spec local-automation.
- [x] Archive.
- [x] Update index.json.
