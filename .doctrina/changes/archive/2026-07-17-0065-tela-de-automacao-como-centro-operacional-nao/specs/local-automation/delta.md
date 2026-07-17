# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

Tela de Automação como centro operacional — o que landou:

- **3 abas** em `Automation.tsx`: Configurar (TargetsCard + EnvCard + token
  GitHub — o token foi extraído do CIPanel via `mode="setup"`), Executar
  (run local + terminal SSE + artefatos + disparo GitHub via `mode="run"`,
  que aponta para a aba Configurar quando falta token) e Histórico.
- **Histórico** (`HistoryCard`): runs recentes local + CI
  (`GET /executions?origin=local_run|github_actions`, mesclados por data)
  com status derivado dos `result_counts`; resumo 30d por repositório
  (runs/falhas/MTTR/última execução) via `GET /metrics/automation` — mesma
  fonte do Dashboard, `name_pattern` configurado aplicado no servidor.
- **Empty states instrutivos**: Executar sem target → "cadastre um target"
  + atalho para Configurar; Histórico sem runs → "dispare o primeiro run" +
  atalho para Executar; primeiro load sem nenhum target abre direto em
  Configurar.
- EARS: novo bullet State-driven (empty state por aba) e Unwanted-behavior
  (setup ≠ operação no mesmo bloco); critério #12; client `api.executions`
  ganhou query string (sem mudança de backend).

Versão `0.5.0` → `0.6.0`.
