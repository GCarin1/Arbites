# ADR 0006 — Coleta CI por artifact Cucumber JSON

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de design do intake; nenhuma implementação ainda (landará com o M4)
- **Landed:** 2026-07-04 — `backend/arbites/ci.py`, `docs/examples/tests.yml`

## Context

Restrição real da API do GitHub Actions (corrigindo suposição da discussão
original): logs completos de um job só ficam disponíveis via API após o
término do job. Ao vivo existe apenas o status de workflow/jobs/steps do
workflow (Checkout, Setup Python, …), não dos steps Gherkin.

## Decision

A coleta de resultados de runs CI é feita por artifact: o workflow roda
`behave -f json`, publica o Cucumber JSON + screenshots como artifact, e o
Arbites baixa, extrai e parseia ao `completed` — com o mesmíssimo parser do
run local. Durante o run, a UI mostra a timeline dos steps do workflow via
polling (10 s, com backoff em rate limit). Alternativa registrada:
self-hosted runner na máquina local — não entra na v1, mas o design de
coleta por artifact funciona igual nos dois casos.

## Alternatives considered

1. Logs ao vivo por step Gherkin — rejeitado: a API do GitHub não fornece
   log de job em andamento.
2. Self-hosted runner local — adiado: registrado como alternativa viável;
   o mecanismo de coleta é o mesmo.

## Consequences

**Positive**

- Um único parser de resultados para local e CI; executions idênticas em
  estrutura.

**Negative**

- Feedback Gherkin só ao fim do workflow; requisitos no repo de automação
  (workflow_dispatch com input de tags + publicação de artifact).

**Neutral**

- Correlação do run por janela de 30 s pós-dispatch (a API não retorna o
  run id do dispatch).
