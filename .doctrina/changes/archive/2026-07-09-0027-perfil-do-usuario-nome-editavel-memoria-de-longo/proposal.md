# Change 0027-perfil-do-usuario-nome-editavel-memoria-de-longo — perfil do usuario: nome editavel + memoria de longo prazo (markdown com Preferencias & Estilo e Contexto Ativo) persistida em profile.md, editavel na UI e injetada como contexto em toda interacao com IA (geracao/revisao/negativos/daily/reuniao)

- **Status:** applied
- **Applied:** 2026-07-09
- **Date:** 2026-07-09
- **Owner:**
- **Affects specs:** profile

## Why

perfil do usuario: nome editavel + memoria de longo prazo (markdown com Preferencias & Estilo e Contexto Ativo) persistida em profile.md, editavel na UI e injetada como contexto em toda interacao com IA (geracao/revisao/negativos/daily/reuniao)

## What

- **api.py** — `GET/PUT /profile` sobre `profile.md` na raiz do workspace
  (frontmatter `name`, corpo = memória; template com "Preferências & Estilo" e
  "Contexto Ativo" criado na primeira leitura); `_with_memory(ws, text)` injeta a
  memória como contexto nos **5 usos de IA** (gerar CTs, revisar, negativos,
  daily, resumo de reunião) — memória vazia/template intocado não injeta nada.
- **Frontend** — nova aba **Perfil** (grupo Suporte): nome editável + editor
  Markdown da memória, salvo em `profile.md`.
- **Testes** — `test_profile.py` (3): template/roundtrip, injeção verificada
  capturando o payload enviado ao provider (RecordingTransport), e memória vazia
  sem bloco de contexto.

## Scope boundaries

- IA editar a própria memória fica no Future da spec (hoje edição manual).
- Sem multiusuário/autenticação (single-user local).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde.
- [x] profile 3/3 no `doctrina coverage` (payload ao provider inspecionado no teste).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
