# Tasks — Change 0067-fix-automacao-target-salvo-com-feature

- [x] Reproduzir em teste: repositório sintético com `.feature` SEM tags de
      CT; confirmado dropdown vazio + 422 no run antes do fix (código lido,
      não hipótese — ver diagnóstico no proposal.md).
- [x] `GET /targets/{name}/features`: listar do glob real
      (`list_feature_files` com local_path/features_glob do target),
      anotando `mapped` (cenários vinculados a CT) vs `scenarios` (total).
- [x] `create_local_run`: permitir rodar `.feature` inteiro sem CTs
      mapeados (gate final vira `not ct_ids and not payload.feature`).
- [x] `gherkin_scan._CT_TAG_RE` → `_ct_tag_re(prefix)` derivada de
      `ws.id_prefixes()["testcase"]`; `scan_target` recebe `Workspace` de
      verdade (o param já existia, só não era usado).
- [x] Achado extra: `behave_json.parse_behave_json` tinha o MESMO hardcode
      (`CT-\d+`) — parametrizado (`ct_prefix`), `runner.py` e `ci.py`
      repassam o prefixo configurado.
- [x] `DEFAULT_FEATURES_GLOB` consolidado em `gherkin_scan.py`, usado em
      `api.py` (browse + modelo `AutomationTargetIn`) em vez de 3 literais
      duplicados.
- [x] UI `Automation.tsx`: option do select mostra `mapped/scenarios`
      quando há não-mapeados; aviso abaixo do select quando o arquivo
      selecionado tem `mapped === 0`.
- [x] Testes de regressão: `test_gherkin.py` (dropdown sem tags + prefixo
      custom no scan), `test_local_runs.py` (run real sem tags, 201 não
      422), `test_behave_json.py` (4 testes unitários do prefixo) — 9 novos
      no total. Suíte completa 225/225 verde.
- [x] `npm run build` limpo + smoke test contra servidor real: browse →
      salvar target → dropdown lista o arquivo com `mapped:0` → run devolve
      201 → behave executa de fato ("1 feature passed").
- [x] Spec local-automation atualizada: critérios #10/#11 novos (verified);
      versão 0.4.0 → 0.5.0.
- [x] Skill adicional avaliada: não necessária — a lição desta mudança já
      está coberta por `fonte-do-preview-diverge-da-fonte-da-operacao`
      (dropdown vs preview) e `novo-consumidor-repassa-config-do-helper`
      (prefixo hardcoded, agora com uma 3ª ocorrência confirmada em
      `behave_json.py`, reforçando o padrão em vez de exigir uma skill
      nova).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0067-fix-automacao-target-salvo-com-feature/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
