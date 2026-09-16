# Change 0179-agente-analise-observabilidade-historico — agente de analise da observabilidade com historico e comparativo entre analises

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** ci-automation

## Why

agente de analise da observabilidade com historico e comparativo entre analises

## What

- `backend/arbites/ci_analise.py` (novo): `dossie()` (recorte do painel, não
  cópia), `dossie_markdown()` (o que vai ao modelo — tabela se lê melhor que
  árvore aninhada e fica auditável), `analisar()`, `listar()`, `ler()` e
  `comparar()`. Modelos `AnaliseObservabilidade` e `ComparativoAnalises`.
- `backend/arbites/api.py`: `POST /ci/analysis`, `GET /ci/analysis`,
  `GET /ci/analysis/{id}` e `POST /ci/analysis/compare`, todas passando pelo
  `_ai_provider` — o interruptor `ai` governa sem regra nova.
- `frontend`: aba **Análise** com gerar, veredito renderizado, histórico em
  tabela e comparativo com melhorou/piorou/continua igual.

## Scope boundaries

- Sem análise automática agendada: analisar é ação de quem está olhando, e um
  cron de IA gastaria token sobre períodos que ninguém pediu.
- O comparativo não calcula veredito no código. `success_rate` subiu e
  `lcp_ms` também não diz se o produto está melhor — isso é julgamento, e
  julgamento é o que se está pedindo ao modelo.
- A retenção (change 0156) não apaga análises: elas são o registro que
  justifica decisão, não dado de telemetria.

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
- [x] Fluxo inteiro exercitado no navegador com provider de IA falso
      (transporte sem rede): gerar → veredito na tela → histórico com duas
      análises → comparar → melhorou/piorou/continua igual. Desktop e 390px.

## Open questions

Nenhuma.
