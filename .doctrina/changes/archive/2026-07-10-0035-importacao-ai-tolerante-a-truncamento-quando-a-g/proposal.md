# Change 0035-importacao-ai-tolerante-a-truncamento-quando-a-g — importacao AI tolerante a truncamento: quando a geracao do modelo local e cortada (timeout) e o JSON externo fica incompleto, recuperar os casos de teste que ja sairam inteiros (_all_objects + _salvage_import) e montar um ImportConversion parcial em vez de falhar sem preview; recuperar folder do cabecalho

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** ai-assist

## Why

importacao AI tolerante a truncamento: quando a geracao do modelo local e cortada (timeout) e o JSON externo fica incompleto, recuperar os casos de teste que ja sairam inteiros (_all_objects + _salvage_import) e montar um ImportConversion parcial em vez de falhar sem preview; recuperar folder do cabecalho

## What

Diagnóstico (log real): gemma-2-9b (sem raciocínio) devolveu JSON válido, mas a
geração de ~15 CTs foi **cortada em 120 s** pelo cliente HTTP → o objeto externo
não fechou → nenhum objeto completo validava → import falhava **sem preview**.

- **backend/arbites/ai.py**
  - `_all_objects(text)` — varre TODO objeto `{…}` (inclusive aninhado), então
    recupera os CTs completos mesmo com o objeto externo truncado.
  - `_salvage_import(text)` — monta um `ImportConversion` parcial com os CTs
    íntegros; recupera `folder` do cabeçalho via regex quando o externo não fecha.
  - `complete(..., salvage=)` — hook: quando nenhum objeto completo valida no
    schema, tenta o salvamento antes de erro.
  - `convert_import` passa `salvage=_salvage_import`.
- **ai-assist spec** MODIFIED (delta) + critério [verified] #7.

## Scope boundaries

- Não implementa streaming nem muda o schema. O caminho feliz (resposta íntegra)
  continua idêntico; salvamento só entra quando a resposta vem cortada.
- O timeout (300 s) e o botão Enviar já vieram na change 0034 — aqui é a
  degradação graciosa quando mesmo assim a geração é truncada.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (116 testes backend + build frontend).
- [x] Critério #7 do ai-assist cita `backend/tests/test_ai_import_robustness.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
