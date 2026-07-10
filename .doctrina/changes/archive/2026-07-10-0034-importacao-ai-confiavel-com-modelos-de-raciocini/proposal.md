# Change 0034-importacao-ai-confiavel-com-modelos-de-raciocini — importacao AI confiavel com modelos de raciocinio (glm-4.7-flash): usar reasoning_content quando content vier vazio, aumentar timeout do cliente HTTP, simplificar prompt de import para nao induzir loop de raciocinio; e no modal de importacao adicionar botao Enviar explicito em vez de submeter no onChange do arquivo

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** ai-assist

## Why

importacao AI confiavel com modelos de raciocinio (glm-4.7-flash): usar reasoning_content quando content vier vazio, aumentar timeout do cliente HTTP, simplificar prompt de import para nao induzir loop de raciocinio; e no modal de importacao adicionar botao Enviar explicito em vez de submeter no onChange do arquivo

## What

- **backend/arbites/ai.py** — `_client` timeout 120→300 s; OpenAICompatible usa
  `reasoning_content` como fallback quando `content` volta vazio (modelos de
  raciocínio como glm-4.7-flash); `_IMPORT_SYSTEM` reescrito curto/determinístico
  para não induzir loop de raciocínio ("manter keyword? PT vs EN?").
- **frontend/src/components/TcRepository.tsx** — modal de importação ganha botão
  **Enviar** explícito; a seleção do arquivo não dispara mais a conversão sozinha;
  aviso de que modelos locais de raciocínio podem levar minutos.
- **ai-assist spec** MODIFIED (delta) + critério [verified] #6.

## Scope boundaries

- Não altera o schema `ImportConversion` nem o fluxo de aceite item-a-item.
- Não tenta impedir que um modelo específico entre em loop de raciocínio (isso
  é do modelo); mitiga com prompt simples, timeout maior e fallback.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest backend + build frontend).
- [x] Critério #6 do ai-assist cita `backend/tests/test_ai_import_robustness.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
