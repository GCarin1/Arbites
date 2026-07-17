# Change 0075-lastreamento-feature-ct-por-nome-de-cenario — Lastreamento .feature-CT por nome de cenario: modal ao buscar .feature lista features e cenarios e o usuario escolhe quais vincular ao Arbites (cria CT automated com automation.feature_path e scenario_name; repositorio de automacao segue read-only, ADR 0003 preservado); sync re-executavel detecta features novos, cenarios novos em features ja vinculados, steps modificados (diff contra o body do CT) e cenarios renomeados ou sumidos (vinculo quebrado), e o modal permite escolher o que criar, atualizar ou re-vincular

- **Status:** proposed
- **Date:** 2026-07-17
- **Owner:**
- **Affects specs:** local-automation

## Why

Lastreamento .feature-CT por nome de cenario: modal ao buscar .feature lista features e cenarios e o usuario escolhe quais vincular ao Arbites (cria CT automated com automation.feature_path e scenario_name; repositorio de automacao segue read-only, ADR 0003 preservado); sync re-executavel detecta features novos, cenarios novos em features ja vinculados, steps modificados (diff contra o body do CT) e cenarios renomeados ou sumidos (vinculo quebrado), e o modal permite escolher o que criar, atualizar ou re-vincular

## What

Vínculo cenário↔CT por NOME (decisão do usuário; repo de automação
segue read-only, ADR 0003 preservado):

- CT ganha `automation.feature_path` + `automation.scenario_name` como
  vínculo alternativo à tag (spec testcases: delta próprio).
- `POST /automation/link-features` (novo): recebe a seleção do modal e
  cria CTs `automated` para os cenários escolhidos (título = nome do
  cenário, body = steps Gherkin verbatim, pasta configurável).
- `GET /automation/sync-status?target=`: compara o estado atual dos
  .feature com os CTs vinculados e classifica: feature novo (nenhum CT),
  cenário novo em feature vinculado, steps modificados (diff dos steps do
  .feature vs body do CT), cenário renomeado/sumido (vínculo quebrado).
- Modal na aba Configurar (botão "Buscar .feature" evolui): lista
  features/cenários com o estado da sync; usuário escolhe o que criar /
  atualizar body / re-vincular (apontar CT para o novo nome) / ignorar.
- Scan (`gherkin_scan`) e tabela `scenarios` passam a registrar também os
  vínculos por nome (schema do índice é descartável, ADR 0001).

## Scope boundaries

O Arbites NÃO escreve tag nem nada no repositório de automação. Vínculo
por nome é frágil por natureza (rename quebra) — mitigação é a sync
explícita (skill vinculo-por-nome-fragil-sync-explicita). A execução ao
vivo fica na 0076.

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
