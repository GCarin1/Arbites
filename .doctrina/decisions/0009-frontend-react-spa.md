# ADR 0009 — Frontend React SPA

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de stack do intake; nenhuma implementação ainda (landará com o M0)
- **Landed:** —

## Context

A UI exige Kanban com drag-and-drop (resultados de execution), alta
densidade de informação (referências: GitHub, Linear, Jira Cloud), design
system próprio dark e atualizações reativas (reindex incremental refletindo
edições externas). O autor domina React.

## Decision

Frontend em React 18 + Vite + TypeScript, SPA servida como estático pelo
próprio FastAPI no build (um comando sobe tudo), com dev mode separado via
Vite. Drag-and-drop com `@dnd-kit/core`; gráficos com `recharts`; design
system próprio (tokens no intake §13): sem emojis, sem gradientes,
espaçamento múltiplo de 4px, status sempre ponto colorido + texto.

## Alternatives considered

1. Jinja + HTMX server-rendered — rejeitado: Kanban drag-and-drop e a
   densidade de UI pretendida exigem SPA; fora do padrão do autor.

## Consequences

**Positive**

- Interações ricas (Kanban, editor, dashboards) com stack dominada pelo
  autor.

**Negative**

- Dois toolchains (Python + Node) e build de frontend no fluxo de release.

**Neutral**

- Em produção local continua um processo único (uvicorn servindo API +
  estáticos em `localhost:8347`).
