# ADR 0002 — ID no frontmatter, nome de arquivo livre

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de design do intake; nenhuma implementação ainda (landará com o M0)
- **Landed:** —

## Context

Artefatos são arquivos que o usuário move, renomeia e reorganiza livremente
(inclusive fora da UI, no Obsidian ou no explorador). Se a identidade do
artefato morasse no nome do arquivo, qualquer rename quebraria vínculos
(story→epic, CT→story, resultado→CT).

## Decision

O ID canônico (`EP-0001`, `ST-0012`, `CT-0001`, …) vive no frontmatter do
arquivo. O nome do arquivo é livre e não carrega semântica; a convenção
`{ID}-{slug}.md` é apenas sugestão de legibilidade.

## Alternatives considered

1. ID no nome do arquivo — rejeitado: rename/move quebraria todos os
   vínculos e exigiria a UI como único ponto de edição.

## Consequences

**Positive**

- Rename e reorganização de pastas nunca quebram a cadeia de
  rastreabilidade.

**Negative**

- Duplicidade de ID é possível (cópia de arquivo); o reindex precisa
  detectá-la e marcar conflito.

**Neutral**

- `counters.json` gerencia a sequência; IDs manuais são aceitos e o
  contador se ajusta no reindex.
