# Change 0089-flaky-visivel-no-ct-e-quarentena-fora-do-pass — flaky visivel no CT e quarentena fora do pass rate

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** testcases, reporting

## Why

`metrics_flaky` já existe no backend e não aparece em lugar nenhum útil:
nem no detalhe do CT, nem como ação. CT instável polui o pass rate e ninguém
vê.

## What

- Badge "flaky" no painel lateral/editor do CT (alternâncias nas últimas N
  execuções, dado do endpoint existente).
- Frontmatter `quarantine: true` no CT (toggle na UI): excluído do pass
  rate e das métricas de cobertura semântica, SEMPRE com contagem visível
  "N em quarentena" no dashboard (nunca esconder silenciosamente).
- Lista de quarentenados acessível do dashboard.

## Scope boundaries

- Sem quarentena automática (decisão humana; o badge só sugere).
- Quarentena não bloqueia execução do CT — só o exclui das métricas.

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] CT alternante ganha badge flaky; `quarantine: true` sai do pass rate e a contagem aparece — `backend/tests/test_metrics.py` + build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
