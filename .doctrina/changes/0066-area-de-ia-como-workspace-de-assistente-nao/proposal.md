# Change 0066-area-de-ia-como-workspace-de-assistente-nao — Area de IA como workspace de assistente (nao cadastro de provider): visao Assistente com exemplos de uso, historico de interacoes, contexto atual ativo, geracao de test cases e revisao do que a IA propos antes de salvar. O usuario deve sentir uma IA que trabalha, nao um formulario de configuracao.

- **Status:** proposed
- **Date:** 2026-07-13
- **Owner:**
- **Affects specs:** ai-assist

## Why

Area de IA como workspace de assistente (nao cadastro de provider): visao Assistente com exemplos de uso, historico de interacoes, contexto atual ativo, geracao de test cases e revisao do que a IA propos antes de salvar. O usuario deve sentir uma IA que trabalha, nao um formulario de configuracao.

## What

Reposiciona a aba de IA (`AiAssist.tsx`) de "cadastro de provider" para
workspace de assistente:

- **Visão Assistente primeiro**: a tela abre no trabalho (gerar/revisar/
  negativos/context pack), não na configuração. Config de providers vira
  seção secundária/colapsada (ou sub-aba "Configuração").
- **Contexto atual ativo**: mostrar o que a IA vai receber junto do pedido —
  memória do perfil ativa (sim/não), recap de decisões+lições recentes
  (quantas — dados do `project_memory.recent_recap`), lições por
  similaridade quando houver. O usuário vê POR QUE a IA responde melhor.
- **Histórico de interações**: reutilizar os `agent_events` (capability
  project-memory, `GET /memory/timeline?kinds=agent`) numa lista na própria
  tela — o que a IA gerou/revisou, quando, sobre o quê. Sem backend novo.
- **Exemplos de uso**: empty state instrutivo por card (ex.: "cole uma
  story ou digite ST-0001") + 1 exemplo clicável que preenche o campo.
- **Revisão antes de salvar**: o fluxo preview→aceite já existe
  (`_preview_out`); torná-lo visualmente explícito — diff/lista do que será
  criado, aceite item a item em destaque.

## Scope boundaries

Não adiciona função de IA nova (gerar/revisar/negativos/import continuam
como estão). Não muda provider/keyring/contratos de API — só a ordem, a
apresentação e a leitura do contexto. O histórico usa o endpoint existente
de timeline (sem endpoint novo). Chat livre com a IA fica para o Future
(fora desta change).

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
