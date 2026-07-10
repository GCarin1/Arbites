# Change 0036-import-quando-o-arquivo-ja-esta-em-gherkin-bdd-p — import: quando o arquivo ja esta em Gherkin/BDD, preservar verbatim (parser deterministico, sem IA e sem exigir provider) em vez de parafrasear via LLM que troca a Feature, remove que, adiciona pontuacao e funde passos And

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** ai-assist

## Why

import: quando o arquivo ja esta em Gherkin/BDD, preservar verbatim (parser deterministico, sem IA e sem exigir provider) em vez de parafrasear via LLM que troca a Feature, remove que, adiciona pontuacao e funde passos And

## What

O usuário reportou que a IA alterava os CTs no import: trocava a Feature
"Pesquisa simples" pelo título do cenário, removia "que", adicionava pontuação
e **fundia dois passos And num só**. Causa: o texto passava pela LLM (extrai em
campos e re-renderiza via `testcase_body_bdd`), o que é intrinsecamente lossy.

- **backend/arbites/ai.py** — `looks_like_gherkin`, `parse_gherkin`,
  `gherkin_body` (reconstrói o corpo só ajustando indentação), `gherkin_folder`
  (slug da Feature). Nada de IA.
- **backend/arbites/api.py** — `/import/ai`: se o arquivo já é Gherkin, usa o
  caminho determinístico (verbatim) ANTES de instanciar o provider; free-form
  continua indo para a LLM.
- **ai-assist spec** MODIFIED (delta) + critério [verified] #8.

## Scope boundaries

- Free-form (não-Gherkin) continua na LLM com todas as defesas anteriores.
- Não trata Background nem Examples de Scenario Outline (v1); passos soltos
  antes do primeiro Scenario são ignorados.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (117 testes backend + build frontend).
- [x] Critério #8 do ai-assist cita `backend/tests/test_ai_import.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
