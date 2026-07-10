# Change 0037-parse-gherkin-nao-tratar-linhas-comecando-com-ou — parse_gherkin: nao tratar linhas comecando com # ou aspas como continuacao de passo — isso colava cabecalhos markdown (### CTxx) e comentarios do documento de origem dentro do ultimo passo do cenario anterior; agora linhas nao reconhecidas sao ignoradas, so tabelas Gherkin de verdade (| a | b |) continuam sendo anexadas

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** ai-assist

## Why

parse_gherkin: nao tratar linhas comecando com # ou aspas como continuacao de passo — isso colava cabecalhos markdown (### CTxx) e comentarios do documento de origem dentro do ultimo passo do cenario anterior; agora linhas nao reconhecidas sao ignoradas, so tabelas Gherkin de verdade (| a | b |) continuam sendo anexadas

## What

Regressão na change 0036: a heurística de "continuação do passo" tratava
qualquer linha começando com `#` ou aspas como comentário/docstring Gherkin e
colava no último passo do cenário atual. O arquivo do usuário usa
`### CTxx - descrição` como separador markdown entre casos — essa linha foi
engolida pelo cenário anterior em vez de ser ignorada.

- **backend/arbites/ai.py** — `parse_gherkin`: remove a heurística `#`/aspas;
  só reconhece passos (`Given/When/Then/And/But/...`) e linhas de tabela real
  (`| a | b |`) como pertencentes ao cenário atual. Qualquer outra linha
  (cabeçalho markdown, comentário, prosa) é silenciosamente ignorada.
- **ai-assist spec** MODIFIED (delta) + critério [verified] #9.

## Scope boundaries

- Não adiciona suporte a `Background`/`Scenario Outline`/`Examples` (fora de
  escopo desta correção pontual).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (118 testes backend + build frontend).
- [x] Critério #9 do ai-assist cita `backend/tests/test_ai_import.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
