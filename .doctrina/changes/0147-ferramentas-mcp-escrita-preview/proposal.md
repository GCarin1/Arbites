# Change 0147-ferramentas-mcp-escrita-preview — ferramentas MCP de escrita com preview e idempotencia pelo vinculo externo

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** mcp-server

## Why

ferramentas MCP de escrita com preview e idempotencia pelo vinculo externo

## What

As ferramentas MCP que **alteram** coisas. Três, e só três:

- `create_or_update_testcase` — grava o caso em BDD, idempotente pelo
  vínculo externo: se já existe vínculo para aquele card, ATUALIZA em vez de
  criar outro.
- `record_result` — resultado de um caso num ciclo, com passos e evidência.
- `link_external` — registra que CT-0007 ↔ CARD-4821 no sistema X.

`link_external` é a mais importante das três, e é a que parece menor. Sem
ela o agente não tem como saber que já criou aquele card: em conversa nova,
sem memória, ele recria — e a duplicata aparece na primeira semana. Com ela
o fluxo vira *"o que daqui ainda não está lá?"* → resposta determinística →
age só no delta. É o que transforma o agente de "cria coisas" em
"sincroniza".

Toda escrita devolve **preview antes de aplicar**, no mesmo padrão que o
import do Xray e a geração por IA já usam: o agente mostra, a pessoa
confirma, e só então grava. A ferramenta declara `write` para que o cliente
MCP saiba pedir confirmação.

E toda escrita passa pelo gate: papel, módulo desligado e log de atividade
com a conta de origem.

**Afeta spec:** `mcp-server`. **ADR:** 0015.

## Scope boundaries

- Não escreve em sistema externo nenhum: quem escreve lá é o agente, com
  o MCP da ferramenta dele.
- Não cria requisito nem execução — só caso, resultado e vínculo. Story
  nasce no sistema oficial ou pela UI.
- Não resolve conflito: se o artefato está em conflito (0145), a escrita é
  recusada com o motivo.

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
- [ ] Chamar `create_or_update_testcase` duas vezes com o mesmo vínculo
      cria UM caso, não dois — a prova de idempotência.
- [ ] Escrita num artefato em conflito é recusada nomeando o conflito.
- [ ] Toda escrita aparece no log de atividade com a conta de origem.
- [ ] O preview mostra o que mudaria antes de qualquer gravação.

## Open questions

Nenhuma.
