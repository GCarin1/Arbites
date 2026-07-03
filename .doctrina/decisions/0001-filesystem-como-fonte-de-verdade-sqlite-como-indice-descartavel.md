# ADR 0001 — Filesystem como fonte de verdade, SQLite como indice descartavel

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de design do intake; nenhuma implementação ainda (landará com o M0)
- **Landed:** —

## Context

Arbites é local-first e os dados pertencem ao usuário (princípios 1–3 do
intake). Os artefatos precisam ser legíveis no Obsidian, versionáveis em
git e sobreviver ao próprio Arbites. Ao mesmo tempo, dashboard e matriz de
rastreabilidade exigem queries relacionais (joins entre stories, CTs,
resultados, evidências) que não são práticas varrendo Markdown a cada
request.

## Decision

O filesystem (Markdown/YAML/JSON/Gherkin em `workspace/`) é a única fonte
de verdade. Um banco SQLite em `.arbites/index.db` serve exclusivamente
como índice de consulta: descartável e integralmente reconstruível via
`arbites reindex`. Apagar o banco nunca perde dados.

## Alternatives considered

1. Banco de dados como fonte de verdade — rejeitado: lock-in, perde
   compatibilidade com Obsidian/git e a portabilidade dos dados.
2. Sem índice, varrendo arquivos por request — rejeitado: métricas e
   matriz de rastreabilidade ficam inviáveis em workspaces com milhares de
   CTs.

## Consequences

**Positive**

- Zero lock-in; workspace editável por qualquer ferramenta externa.
- Recuperação trivial de corrupção do índice (reindex).

**Negative**

- Toda escrita tem dois passos (disco + índice); reindex incremental via
  watchdog é obrigatório para a UI refletir edições externas.

**Neutral**

- O esquema SQLite pode mudar livremente entre versões, pois o banco é
  descartável.
