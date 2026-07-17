# Tasks — Change 0065-tela-de-automacao-como-centro-operacional-nao

- [x] Reorganizar `Automation.tsx` em 3 abas (estado local, `.tab-bar` no
      CSS); primeiro load sem targets abre em Configurar.
- [x] Aba Configurar: TargetsCard + EnvCard + token GitHub (extraído do
      CIPanel via prop `mode="setup"` — setup separado da operação sem
      duplicar o estado do componente).
- [x] Aba Executar: run local + terminal + ArtifactsCard + CIPanel
      `mode="run"` (avisa e aponta para Configurar quando falta token);
      empty state instrutivo sem targets.
- [x] Aba Histórico (`HistoryCard`): runs recentes local+CI mesclados
      (`GET /executions?origin=`) com status por `result_counts`; resumo
      30d por repo (runs/falhas/MTTR/última) via `GET /metrics/automation`;
      empty state instrutivo sem runs.
- [x] Client `api.executions(query)` (query string; sem mudança de backend
      — endpoints já existiam e são cobertos por
      `test_executions.py`/`test_automation_report.py`).
- [x] `npm run build` limpo + smoke real dos endpoints consumidos.
- [x] Spec local-automation: EARS + critério #12; versão 0.5.0 → 0.6.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-17-0065-tela-de-automacao-como-centro-operacional-nao/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
