# Change 0054-health-score-nota-unica-0-100-no-dashboard-compo — Health Score: nota unica 0-100 no Dashboard, composta de cobertura (media requisito+execucao), defeitos (penalidade por severidade), automacao (pass rate dos runs de CI/local) e divida de testes (bloqueio+retrabalho+flaky). GET /metrics/health devolve score + componentes com formula e peso explicitos (nada escondido atras do numero). Pesos configuraveis em arbites.yaml (health_score.weights), com default 30/25/25/20 renormalizado; componente sem dado nao participa (nao vira zero, workspace vazio nao pontua). Card em destaque no topo do Dashboard

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** reporting

## Why

Health Score: nota unica 0-100 no Dashboard, composta de cobertura (media requisito+execucao), defeitos (penalidade por severidade), automacao (pass rate dos runs de CI/local) e divida de testes (bloqueio+retrabalho+flaky). GET /metrics/health devolve score + componentes com formula e peso explicitos (nada escondido atras do numero). Pesos configuraveis em arbites.yaml (health_score.weights), com default 30/25/25/20 renormalizado; componente sem dado nao participa (nao vira zero, workspace vazio nao pontua). Card em destaque no topo do Dashboard

## What

Terceira das 6 ideias: nota única 0-100 sobre a saúde de QA, defensável em
reunião — cada componente cita a própria fórmula e peso, nada escondido.

- **backend/arbites/metrics.py** — `health_score(conn, weights, sprint, days,
  squad)`: 4 componentes (`coverage`, `defects`, `automation`, `debt`), cada
  um reusando métricas já existentes (`requirement_coverage`,
  `execution_coverage`, `defects_report`, `automation_report`,
  `blocked_rate`, `rework_rate`, `flaky`) — nenhum dado novo persistido.
  Pesos default 30/25/25/20, configuráveis e renormalizados. Um componente
  sem dado disponível (`value: None`) NÃO conta como zero — fica de fora do
  cálculo, com os pesos dos demais renormalizados.
- **backend/arbites/api.py** — `GET /metrics/health` lendo
  `health_score.weights` do `arbites.yaml`.
- **frontend** — `HealthScore`/`HealthComponent` types, `api.metricsHealth`,
  `HealthScoreCard` (nota grande + 4 sub-cards com tooltip da fórmula) em
  destaque no topo do Dashboard, antes dos demais cards de métrica.
- **reporting spec** MODIFIED (delta) + critério [verified] #12.

## Bug corrigido no processo

`defects_pct = max(0, 100 - penalty)` sempre tinha um valor — com ZERO
defeitos, `penalty=0` → `defects_pct=100`, mesmo num workspace completamente
vazio (sem nenhum CT criado). Isso faria um workspace recém-criado, sem
NADA feito ainda, mostrar "Health Score: 100" — um falso positivo de saúde.
Corrigido: `defects_pct` só recebe valor se existe pelo menos um CT OU
defeito no workspace; senão fica `None` (mesma semântica dos outros 3
componentes), e o score geral de um workspace vazio vira `null` (verificado
por teste e por smoke contra servidor real).

## Scope boundaries

- "Builds" e "Automações" (do doc de ideias) foram unificados num único
  componente `automation` — o Arbites não distingue build puro de execução
  de automação; ambos são runs `origin != manual`. Anotado explicitamente,
  não escondido.
- Nenhum dado novo persistido — tudo derivado das métricas já existentes.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (171 testes backend + build frontend).
- [x] Critério #12 do reporting cita `backend/tests/test_health_score.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
