# Change 0030-importacao-inteligente-em-massa-upload-de-txt-md — importacao inteligente em massa: upload de txt/md/xml com casos de teste em formato livre; a IA identifica cada caso, sugere uma pasta pelo contexto e converte para BDD (Given/When/Then) em preview aceitavel item a item; prompt otimizado para modelos de ate 9B

- **Status:** proposed
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** ai-assist

## Why

importacao inteligente em massa: upload de txt/md/xml com casos de teste em formato livre; a IA identifica cada caso, sugere uma pasta pelo contexto e converte para BDD (Given/When/Then) em preview aceitavel item a item; prompt otimizado para modelos de ate 9B

## What

- **ai.py** — schema `ImportConversion` (folder sugerido + testcases),
  `convert_import` com prompt curto (9B-friendly, texto truncado a 24k chars) e
  `testcase_body_bdd` (render Gherkin: Given=pré-condições, When=passos,
  Then=resultado esperado).
- **api.py** — `POST /import/ai` (upload .txt/.md/.xml; 422 p/ extensão
  inválida/vazio; memória do perfil injetada; preview puro).
- **Frontend** — botão **Importar com IA** no repositório de test cases: modal
  com upload, pasta sugerida editável e preview BDD aceitável item a item
  (aceite = POST /testcases na pasta).
- **Testes** — `test_ai_import.py` (2).

## Scope boundaries

- Sem parse determinístico de XML (quem interpreta é a IA — o formato de
  entrada é livre por definição). Import estruturado do Xray continua na
  capability `xray-migration`.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build + pytest verdes.
- [x] ai-assist 4/4 no coverage.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
