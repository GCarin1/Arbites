# Change 0063-dashboard-executivo-transformar-a-dashboard-de — Dashboard executivo: transformar a dashboard de vitrine de metrica em painel de decisao. Tendencia com variacao vs periodo anterior; alertas de risco; bloco ultima-atualizacao-dos-dados; secao top-problemas; secao acoes-recomendadas. Responder: estamos entregando bem? onde esta o risco? o que piorou? qual area esta mais instavel? o que mudou nos ultimos 7/30 dias?

- **Status:** applied
- **Applied:** 2026-07-17
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** reporting

## Why

Dashboard executivo: transformar a dashboard de vitrine de metrica em painel de decisao. Tendencia com variacao vs periodo anterior; alertas de risco; bloco ultima-atualizacao-dos-dados; secao top-problemas; secao acoes-recomendadas. Responder: estamos entregando bem? onde esta o risco? o que piorou? qual area esta mais instavel? o que mudou nos ultimos 7/30 dias?

## What

Evolui a Dashboard de "vitrine de métrica" para painel de decisão. Backend
(`metrics.py` + rotas em `api.py`) e frontend (`Dashboard.tsx`):

- **Variação vs período anterior**: cada métrica do summary ganha
  `previous`/`delta` comparando a janela atual (7/15/30d) com a janela
  imediatamente anterior — responde "o que piorou?". Provável
  `GET /metrics/summary?compare=1` ou campo novo no summary.
- **Alertas de risco**: bloco no topo derivado do que já existe — Health
  Score baixo/em queda, repositório de automação quebrado (`broken_since`),
  defeitos críticos envelhecendo, CTs flaky — cada alerta clicável para a
  seção correspondente. Reutiliza `audit.collect_findings` (achados bad)
  em vez de heurística nova.
- **Última atualização dos dados**: expor `index_meta.last_reindex` no
  Dashboard ("dados de HH:MM") — o dado já existe no `GET /workspace`.
- **Top problemas**: seção com os N piores itens (piores repos de automação,
  CTs que mais falham, defeitos mais velhos) — todos dados que os reports
  atuais já devolvem, hoje espalhados.
- **Ações recomendadas**: lista curta derivada por regra (não IA): ex.
  "3 stories sem CT → criar cobertura", "repo X quebrado há 5d → investigar
  run", "defeito DF-Y aberto há 30d sem causa raiz → registrar lição".

## Scope boundaries

Não cria métrica nova de coleta — só agrega/compara o que o índice já tem.
Ações recomendadas são regras determinísticas (sem chamada de IA; uma versão
IA fica para o Future). A hierarquia visual do layout em si é da change 0060
(design-system) — esta change entrega o CONTEÚDO executivo; se 0060 landar
antes, os blocos novos já nascem na gramática canônica.

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

<!-- List unresolved decisions. Empty if none. -->
