# Tasks — Change 0066-area-de-ia-como-workspace-de-assistente-nao

- [x] Reordenar `AiAssist.tsx`: Contexto ativo → Gerar → Revisar → Context
      Pack → Histórico; `ProvidersCard` colapsado atrás do botão
      "Configuração" no page-head.
- [x] `AssistContextCard`: memória do perfil (detecção estrutural de
      template intocado), decisões aceitas no recap, lições aprendidas —
      via `/profile`, `/decisions?status=accepted`,
      `/defects?has_lesson=true` (client `api.profile()` novo).
- [x] `AssistHistoryCard`: agent_events via
      `GET /memory/timeline?kinds=agent` (endpoint da project-memory, sem
      backend novo); oculto quando vazio.
- [x] Exemplo de uso clicável no GenerateCard (story genérica, sem nomes
      reais) quando o campo está vazio.
- [x] Preview explícito: banner status-dot "em PREVIEW — nada gravado,
      aceite item a item" no PreviewList.
- [x] `npm run build` limpo + smoke real dos endpoints consumidos (profile
      devolve template → "vazia"; decisions accepted conta; timeline agent
      vazia → card oculto).
- [x] Spec ai-assist: EARS State-driven + critério #12; versão 0.10.0 →
      0.11.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-17-0066-area-de-ia-como-workspace-de-assistente-nao/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
