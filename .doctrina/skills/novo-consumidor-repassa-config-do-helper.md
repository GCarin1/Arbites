---
name: novo-consumidor-repassa-config-do-helper
description: Ao reutilizar um helper que aceita config opcional (regex, threshold, prefixo), todo consumidor NOVO deve repassar a mesma config que o call site original passa — chamar com o default silenciosamente diverge do comportamento que o usuário configurou.
when: O agente está adicionando um novo call site para uma função existente cuja assinatura tem parâmetro opcional vindo de configuração do usuário (arbites.yaml ou similar).
---

# Skill — novo-consumidor-repassa-config-do-helper

## When to use this skill

- O agente vai chamar uma função existente que tem parâmetro opcional com
  default (ex.: `automation_report(conn, name_pattern=None, ...)`) a partir
  de um módulo/feature novo.
- O agente está revisando código que reutiliza um helper "config-aware" —
  qualquer função cujo call site original lê algo de `ws.config()` antes de
  chamar.

## Procedure

1. Antes de chamar o helper, grep pelos call sites existentes:
   `grep -n "nome_do_helper(" backend/arbites/*.py`. Se algum call site lê
   config antes de chamar (ex.:
   `pattern = (ws.config().get("ci_monitoring") or {}).get("name_pattern")`),
   esse é o CONTRATO real da função — o default `None` é fallback, não o
   comportamento canônico.
2. Propague o parâmetro pela cadeia: o endpoint (que tem acesso a `ws`) lê a
   config UMA vez e repassa; funções puras de domínio (`metrics`, `audit`,
   `risk_map`) recebem o valor por parâmetro, nunca leem config diretamente
   (mantém as funções testáveis com `conn` puro).
3. Escreva um teste de regressão com a config CUSTOMIZADA (não o default):
   configure um padrão/prefixo diferente no `arbites.yaml` do workspace de
   teste e assert que a feature nova continua funcionando. O default passa
   sempre — só a config custom pega esse bug.
4. Cheque os primos: se o helper depende de config, outros valores
   configuráveis usados por perto provavelmente também
   (ex.: `id_prefixes.defect` além de `ci_monitoring.name_pattern`) —
   hardcodar `DF-` num módulo novo é a mesma classe de bug.

## Anti-patterns

- `automation_report(conn)` chamado de 3 features novas (health_score,
  audit, risk_map) enquanto o endpoint original passava
  `ci_monitoring.name_pattern` — com padrão customizado, o componente de
  automação do Health Score virava `None`, o auditor nunca achava automação
  quebrada e o risk map perdia o pass rate. Tudo silencioso: sem erro, só
  dado ausente (bug real, change 0059).
- Regex `\bDF-\d+\b` hardcoded num módulo novo quando o prefixo de defeito
  é `id_prefixes.defect` configurável (mesma change).
- Fazer o módulo de domínio ler `ws.config()` diretamente "para não esquecer
  o parâmetro" — acopla a função ao workspace e esconde a dependência da
  assinatura.

## Related material

- `backend/arbites/api.py` — endpoints `metrics_health`, `_run_audit`,
  `get_risk_map` (leitura única da config, repasse por parâmetro).
- `.doctrina/changes/archive/2026-07-13-0059-fix-varredura-de-inconsistencias-entre/`
- [[formato-especifico-do-usuario-vira-config-regex]] — a origem do
  `name_pattern` configurável que este bug esqueceu de repassar.
