# Change 0114-dashboard-com-kpis-e-o-que-precisa-de-atencao — Dashboard com KPIs e o que precisa de atencao

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain; signals: para que)
- **Affects specs:** reporting

## Why

Reorganizar o dashboard no padrao das ferramentas de mercado: uma linha de indicadores no topo com os numeros que ja sao apurados, e logo abaixo um bloco em prosa dizendo o que precisa de atencao, alimentado pelo resumo executivo de IA que ja existe, para que o numero venha acompanhado da leitura dele.

## What

- `reporting` (spec MODIFIED): a ordem de leitura do dashboard — número no
  topo, leitura do número logo abaixo — e a degradação sem IA.
- `frontend/src/components/Dashboard.tsx`: a linha de indicadores e o bloco
  "O que precisa de atenção", que cai nos achados determinísticos quando não
  há provider.
- `backend/tests/test_dashboard_attention.py`: a prova de que o contexto do
  bloco sai dos números já apurados e de que o dashboard inteiro responde
  com a IA desligada.
- Nenhuma métrica nova e nenhum endpoint novo.

## Scope boundaries

- Não cria métrica: a linha de indicadores só reordena o que
  `GET /metrics/summary` e `GET /metrics/health` já devolvem.
- Não mexe no cálculo do health score, do pass rate nem dos thresholds.
- Não remove os painéis de baixo (tendência, automação, mapa de risco,
  defeitos, matriz); eles descem, não somem.
- Não torna a IA obrigatória em lugar nenhum do produto.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

Nenhuma.
