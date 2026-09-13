# Tasks — Change 0137-cenario-interrompido-timeout-cancelamento

- [x] Reproduzir: rodar o cenário de 30 s com timeout de 3 s e registrar que
      o resultado sai `passed` mesmo com o run em `timeout`.
- [x] Dar `interrupted` a `_live_conclude` e propagar de `_run_one` via
      `_collect` quando o run foi morto por timeout ou cancelamento.
- [x] Escrever o teste de regressão que prende "cenário morto no meio não
      vira passed".
- [x] Confirmar que o teste novo falha contra o código antigo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0137-cenario-interrompido-timeout-cancelamento/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
