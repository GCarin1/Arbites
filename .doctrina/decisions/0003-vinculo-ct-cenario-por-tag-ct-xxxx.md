# ADR 0003 — Vinculo CT-cenario por tag @CT-XXXX

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de design do intake; nenhuma implementação ainda (landará com o M3)
- **Landed:** 2026-07-04 — `backend/arbites/gherkin_scan.py`

## Context

CTs `automated`/`hybrid` precisam apontar para um cenário Gherkin em um
repositório de automação separado, que o Arbites nunca escreve (read-only).
O elo precisa sobreviver a refactors do repo de automação (renomear
features, mover arquivos, reescrever cenários).

## Decision

O vínculo é a tag `@CT-XXXX` no cenário Gherkin. No reindex, o Arbites
escaneia o `features_glob` de cada target e monta o mapa
`@CT-XXXX → (feature_file, scenario_name, line)`. Tag duplicada em dois
cenários é erro; tag sem CT é warning "cenário órfão"; CT automatizado sem
tag é warning "automação quebrada".

## Alternatives considered

1. Convenção por nome ou caminho do arquivo — rejeitada: implícita e
   frágil; qualquer refactor do repo de automação quebraria o vínculo
   silenciosamente.

## Consequences

**Positive**

- Vínculo explícito e estável; sobrevive a refactor do repo de automação.
- Filtro de execução (`--tags=@CT-0001`) cai de graça no Behave.

**Negative**

- Exige disciplina de tagging no repo de automação; mitigado pelos
  warnings de integridade do reindex.

**Neutral**

- O mesmo mecanismo serve qualquer runner que suporte tags (princípio
  "adaptadores, não integrações exclusivas").
