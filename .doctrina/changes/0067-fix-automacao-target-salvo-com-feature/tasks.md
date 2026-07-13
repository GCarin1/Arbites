# Tasks — Change 0067-fix-automacao-target-salvo-com-feature

- [ ] Reproduzir em teste: repositório sintético em tmp_path com `.feature`
      SEM tags de CT (caminho com espaços/acentos/vírgulas no fixture);
      confirmar dropdown vazio + 422 no run (o bug).
- [ ] `GET /targets/{name}/features`: listar do glob real
      (`list_feature_files` com local_path/features_glob do target),
      anotando cenários mapeados vs não-mapeados por arquivo.
- [ ] `create_local_run`: permitir rodar `.feature` inteiro sem CTs
      mapeados (execution sem vínculo ou com resultado "não mapeado"
      explícito) — behave já suporta o arquivo posicional.
- [ ] `_CT_TAG_RE` → regex derivada de `id_prefixes.testcase` configurado
      (repassar prefixo ao `scan_target`/`gherkin_scan`, mesma família da
      0059; ver skill novo-consumidor-repassa-config-do-helper).
- [ ] UI `Automation.tsx`: quando há features sem cenários tagueados,
      mostrar contagem + orientação (taguear p/ rastreabilidade ou rodar o
      arquivo inteiro) em vez de select vazio.
- [ ] Testes de regressão (dropdown com repo sem tags; run por arquivo sem
      CTs; prefixo custom no scan) + suíte completa verde.
- [ ] `npm run build` limpo + smoke test contra servidor real com repo
      sintético.
- [ ] Atualizar spec local-automation: critérios novos → verified; bump.
- [ ] Avaliar skill adicional se a implementação revelar lição além da já
      capturada em fonte-do-preview-diverge-da-fonte-da-operacao.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0067-fix-automacao-target-salvo-com-feature/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
