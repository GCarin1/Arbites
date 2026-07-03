# ADR 0007 — Jira fora de escopo, Xray como migracao pontual

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de escopo do intake; a migração landará com o M2
- **Landed:** —

## Context

A empresa descomissionará Jira e Xray em favor do Businessmap. Integração
contínua com sistemas que vão morrer é esforço perdido; porém a base de
testes existente no Xray precisa ser resgatada enquanto ainda há acesso.

## Decision

Integração Jira: fora de escopo permanente. Xray: ferramenta de migração
pontual com prazo (import XML com preview e idempotência por
`external_key`), posicionada cedo na ordem de entrega (M2, antes da
automação) para não perder a janela. Businessmap fica como única
integração externa de longo prazo (M6, a especificar quando a migração
corporativa se concretizar).

## Alternatives considered

1. Integração contínua com Jira/Xray — rejeitada: descomissionamento
   corporativo confirmado.

## Consequences

**Positive**

- Nenhum esforço em integrações condenadas; janela de migração protegida.

**Negative**

- Referências externas (`external_key`) ficam textuais e não validadas até
  o M6.

**Neutral**

- O export do XML do Xray pode (e deve) ser feito já, antes mesmo do M2
  existir.
