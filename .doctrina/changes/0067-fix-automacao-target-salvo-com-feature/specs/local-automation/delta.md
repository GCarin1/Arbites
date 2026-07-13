# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Fix: seleção e execução de `.feature` em repositório SEM cenários tagueados
`@CT-`:

### Ubiquitous

- The system shall listar no dropdown de features do run os arquivos
  `.feature` reais que o glob do target resolve no disco (mesma fonte do
  preview de browse), anotando por arquivo quantos cenários estão mapeados
  a CTs e quantos não — nunca uma lista vazia quando o disco tem features.
- The system shall derivar do prefixo de CT CONFIGURADO
  (`id_prefixes.testcase`) tanto a regex de tag de cenário do scan
  (`gherkin_scan`) quanto o parser de resultado do Behave
  (`behave_json.parse_behave_json`, usado no run local e na coleta de CI) —
  nenhum dos dois hardcoda `CT-`.

### Event-driven

- When o usuário roda um `.feature` inteiro cujos cenários não têm tag de
  CT, the system shall executar o arquivo mesmo assim (execution sem CTs
  vinculados), em vez de recusar com `422 empty_selection`.
- When um target tem features no glob mas nenhum cenário tagueado, the
  system shall explicar isso na UI (contagem de cenários sem tag), em vez
  de exibir apenas um select vazio.

### Unwanted-behavior (must-not)

- The system shall not usar fontes divergentes para o preview e para a
  operação da mesma lista — o que o browse mostra é o que o dropdown do
  run oferece.

### Acceptance criteria (a acrescentar)

- [verified] Target salvo apontando para um repositório de features SEM
  tags de CT: o dropdown lista o arquivo (com `mapped: 0`) e rodar o
  arquivo inteiro cria a execution (201, sem CTs vinculados) e dispara o
  behave de verdade — verified by
  `backend/tests/test_gherkin.py::test_target_features_lists_disk_files_even_without_any_tagged_scenario`
  e
  `backend/tests/test_local_runs.py::test_run_whole_feature_without_any_ct_tag_does_not_422`.
- [verified] Com `id_prefixes.testcase` customizado, cenários tagueados com
  o prefixo configurado são mapeados pelo scan E pelo parser de resultado
  do Behave — verified by
  `backend/tests/test_gherkin.py::test_scan_recognizes_scenario_tag_with_custom_testcase_prefix`
  e `backend/tests/test_behave_json.py`.
