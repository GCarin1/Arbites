# ADR 0010 — Sprint e ambiente como texto livre na v1

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de modelo de dados do intake; nenhuma implementação ainda (landará com o M1)
- **Landed:** —

## Context

Executions carregam `sprint` e `environment` para filtros e métricas.
Criar cadastro de sprints/releases adicionaria burocracia (telas, CRUD,
vínculos) sem valor na v1 single-user — o tipo de inchaço que matou o
Probatio.

## Decision

`sprint` e `environment` são texto livre no `execution.json` na v1. Sem
cadastro, sem validação de existência. Filtros de métricas agrupam por
igualdade de string.

## Alternatives considered

1. Cadastro de sprints/releases com entidade própria — rejeitado na v1:
   burocracia sem retorno; estrutura pode vir depois sem migração de dados
   (strings continuam válidas).

## Consequences

**Positive**

- Zero fricção ao criar executions; menos telas e entidades.

**Negative**

- Typos fragmentam filtros ("Sprint 42" vs "sprint42"); aceito na v1
  single-user.

**Neutral**

- Estruturar depois é aditivo: as strings existentes viram referências.
