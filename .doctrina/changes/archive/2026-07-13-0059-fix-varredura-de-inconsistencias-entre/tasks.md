# Tasks — Change 0059-fix-varredura-de-inconsistencias-entre

- [x] P1: `health_score`/`audit`/`risk_map` aceitam e recebem
      `ci_monitoring.name_pattern` dos endpoints (`metrics.py`, `audit.py`,
      `risk_map.py`, `api.py`).
- [x] P2: `Memory.tsx` — seleção vazia de tipos mostra lista vazia em vez de
      chamar a API sem filtro (que devolve tudo).
- [x] P3: `risk_map` usa `id_prefixes.defect` configurado na regex de menção
      a defeito (`_defect_re`), não mais `DF-` fixo.
- [x] P4: `_log_agent_event` não-fatal — falha vira `log.warning`, resposta
      da IA preservada (novo logger `arbites` em `api.py`).
- [x] P5: `_broken_automations` captura `TypeError` (created_at naive
      editado externamente) além de `ValueError`.
- [x] P6: `risk_map.build` computa `automation_report` uma vez por
      requisição e repassa `pass_rate_by_repo` aos scans.
- [x] 5 testes de regressão (health_score, audit ×2, risk_map ×2,
      project_memory) + suíte completa 218/218 verde.
- [x] `npm run build` limpo.
- [x] Specs atualizadas: reporting 0.10.1, audit 0.1.1, risk-map 0.1.1,
      project-memory 0.1.1 (EARS + critérios novos).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-12-0059-fix-varredura-de-inconsistencias-entre/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
