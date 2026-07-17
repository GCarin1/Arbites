# Spec Delta — capability: ai-assist

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/ai-assist/spec.md`

---

Área de IA como workspace de assistente — o que landou:

- **Visão de trabalho primeiro**: `AiAssist.tsx` reordenado — Contexto
  ativo → Gerar → Revisar → Context Pack → Histórico; `ProvidersCard` fica
  atrás do botão "Configuração" (colapsado).
- **Contexto ativo** (`AssistContextCard`): mostra o que acompanha cada
  pedido — memória do perfil preenchida ou não (detecção estrutural:
  template intocado ≠ preenchido, sem duplicar a string do template),
  quantas decisões aceitas entram no recap
  (`GET /decisions?status=accepted`) e quantas lições aprendidas existem
  (`GET /defects?has_lesson=true`).
- **Histórico de interações** (`AssistHistoryCard`): agent_events da
  capability `project-memory` via `GET /memory/timeline?kinds=agent` — sem
  endpoint novo; oculto quando vazio.
- **Exemplo de uso clicável** no GenerateCard (preenche com uma story
  genérica) quando o campo está vazio.
- **Preview explícito**: banner com status-dot "N item(ns) em PREVIEW —
  nada foi gravado; aceite item a item" (reforço do fluxo `_preview_out`
  existente).
- Client: `api.profile()` novo; EARS State-driven + critério #12.

Versão `0.10.0` → `0.11.0`.
