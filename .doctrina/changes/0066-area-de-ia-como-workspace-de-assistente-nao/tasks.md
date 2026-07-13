# Tasks — Change 0066-area-de-ia-como-workspace-de-assistente-nao

- [ ] Reordenar `AiAssist.tsx`: visão de trabalho primeiro (gerar/revisar/
      negativos/context pack); `ProvidersCard` vira seção
      colapsada/secundária ("Configuração").
- [ ] Card "Contexto ativo": memória do perfil (ativa?), recap de
      decisões+lições recentes (contagem via dados existentes), lições por
      similaridade — o que a IA vai receber junto do pedido.
- [ ] Histórico de interações: lista dos agent_events via
      `GET /memory/timeline?kinds=agent` (client `memoryTimeline` já
      existe), com alvo clicável.
- [ ] Exemplo de uso clicável por função (preenche o campo com um exemplo
      genérico — sem nomes de empresa/projeto reais).
- [ ] Preview explícito antes do aceite: lista/diff do que será criado,
      aceite item a item em destaque (reforçar o fluxo `_preview_out`
      existente na UI).
- [ ] Suíte completa verde + `npm run build` limpo + smoke test.
- [ ] Atualizar spec ai-assist: critérios #11/#12 → verified; bump minor.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0066-area-de-ia-como-workspace-de-assistente-nao/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
