# Change 0059-fix-varredura-de-inconsistencias-entre — fix: varredura de inconsistencias entre capabilities novas e infra existente. (1) health_score, audit e risk_map chamavam automation_report sem o ci_monitoring.name_pattern configurado - com padrao customizado o componente de automacao do Health Score vira null, o auditor nunca acha automacao quebrada e o risk map perde o pass rate, tudo silencioso; (2) Memoria do Projeto: desmarcar todos os filtros de tipo mostrava TUDO em vez de nada (lista vazia virava param vazio = sem filtro); (3) prefixo de defeito DF- hardcoded no risk_map apesar de id_prefixes.defect ser configuravel; (4) falha ao gravar o log de agente derrubava a resposta da IA ja gerada; (5) TypeError nao capturado no audit com created_at naive editado externamente; (6) automation_report recomputado por repo no risk_map.build

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** reporting

## Why

fix: varredura de inconsistencias entre capabilities novas e infra existente. (1) health_score, audit e risk_map chamavam automation_report sem o ci_monitoring.name_pattern configurado - com padrao customizado o componente de automacao do Health Score vira null, o auditor nunca acha automacao quebrada e o risk map perde o pass rate, tudo silencioso; (2) Memoria do Projeto: desmarcar todos os filtros de tipo mostrava TUDO em vez de nada (lista vazia virava param vazio = sem filtro); (3) prefixo de defeito DF- hardcoded no risk_map apesar de id_prefixes.defect ser configuravel; (4) falha ao gravar o log de agente derrubava a resposta da IA ja gerada; (5) TypeError nao capturado no audit com created_at naive editado externamente; (6) automation_report recomputado por repo no risk_map.build

## What

<!-- The shape of the change: artifacts created or modified, specs affected. -->

## Scope boundaries

<!-- Anything adjacent that this change deliberately does NOT touch. -->

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
