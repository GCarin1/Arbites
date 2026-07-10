# Change 0047-perfil-heatmap-de-atividade-estilo-github-contri — perfil: heatmap de atividade estilo GitHub (contribution graph) com a atividade de QA do projeto. Novo GET /metrics/activity agrega por dia os ultimos ~12 meses (janela alinhada a segunda-feira): casos executados (transicoes de resultado), bugs abertos, CTs/requisitos criados e runs de automacao; devolve so os dias com atividade. Componente ActivityHeatmap na pagina de Perfil (grade Seg-Dom x semanas, cores no verde do projeto por intensidade, seletor de metrica, tooltips)

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** reporting

## Why

perfil: heatmap de atividade estilo GitHub (contribution graph) com a atividade de QA do projeto. Novo GET /metrics/activity agrega por dia os ultimos ~12 meses (janela alinhada a segunda-feira): casos executados (transicoes de resultado), bugs abertos, CTs/requisitos criados e runs de automacao; devolve so os dias com atividade. Componente ActivityHeatmap na pagina de Perfil (grade Seg-Dom x semanas, cores no verde do projeto por intensidade, seletor de metrica, tooltips)

## What

Heatmap de contribuições estilo GitHub na página de Perfil, mas com a
atividade de QA do projeto (não do GitHub) — tudo derivado de sinais datados
que já existem no índice.

- **backend/arbites/metrics.py** — `activity_heatmap(conn, days=371)`: janela
  dos últimos ~12 meses ALINHADA à segunda-feira (para a grade Seg→Dom ×
  semanas), agregando por dia 5 fontes: casos executados (`result_events`),
  bugs abertos (`defects.opened_at`), CTs criados (`testcases.created`),
  requisitos criados (`requirements.created`) e runs de automação
  (`executions` não-manuais). Devolve só os dias com atividade + os totais.
- **backend/arbites/api.py** — `GET /metrics/activity?days=`.
- **frontend/src/components/ActivityHeatmap.tsx** (novo) — grade Seg→Dom ×
  semanas, rótulos de mês, seletor de métrica (toda atividade / casos
  executados / bugs / CTs / requisitos / runs), tooltip por dia e legenda
  menos→mais. Intensidade em 5 níveis no VERDE DO PROJETO
  (`color-mix(--success, --surface)`), adaptando a claro/escuro.
- **frontend/src/components/Profile.tsx** — renderiza o heatmap.
- **reporting spec** MODIFIED (delta) + critério [verified] #10.

Genérico: nenhuma referência a empresa/projeto; usa as cores do próprio app.

## Scope boundaries

- "Casos executados" = cada transição de resultado (`result_events`); não
  deduplica re-execuções do mesmo CT no dia — é atividade, não cobertura.
- Cobertura ao longo do tempo (um dos exemplos citados) é métrica de
  ponto-no-tempo, não um evento diário — fora deste heatmap de contribuições;
  a tendência de pass/fail já vive no Dashboard.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (150 testes backend + build frontend).
- [x] Critério #10 do reporting cita `backend/tests/test_activity_heatmap.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
