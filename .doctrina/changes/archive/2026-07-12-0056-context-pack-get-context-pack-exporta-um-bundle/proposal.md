# Change 0056-context-pack-get-context-pack-exporta-um-bundle — Context Pack: GET /context-pack exporta um bundle Markdown unico (RAG-ready) com requisitos, casos de teste, defeitos (causa raiz/correcao quando registrados) e decisoes arquiteturais relevantes a um escopo (epic, story ou squad), para uso por agentes de IA externos (Cursor, Claude Code, Codex, Roo Code, Aider). Reaproveita a matriz de rastreabilidade como esqueleto e enriquece cada no com o corpo Markdown lido do disco. Exige ao menos um filtro de escopo (422 sem epic/story/squad) para nao despejar o workspace inteiro sem querer. Botao 'Baixar Context Pack' na aba de IA (nao depende de provider de IA configurado, e um export puro).

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** context-pack

## Why

Context Pack: GET /context-pack exporta um bundle Markdown unico (RAG-ready) com requisitos, casos de teste, defeitos (causa raiz/correcao quando registrados) e decisoes arquiteturais relevantes a um escopo (epic, story ou squad), para uso por agentes de IA externos (Cursor, Claude Code, Codex, Roo Code, Aider). Reaproveita a matriz de rastreabilidade como esqueleto e enriquece cada no com o corpo Markdown lido do disco. Exige ao menos um filtro de escopo (422 sem epic/story/squad) para nao despejar o workspace inteiro sem querer. Botao 'Baixar Context Pack' na aba de IA (nao depende de provider de IA configurado, e um export puro).

## What

Nova capability `context-pack`. Backend: `backend/arbites/context_pack.py`
(`build()`, reaproveita `metrics.traceability` + carrega o corpo de cada
requisito/CT/decisão do disco), endpoint `GET /context-pack` em `api.py`
(`epic`/`story`/`squad`, 422 sem nenhum). Frontend:
`ContextPackCard` em `AiAssist.tsx` (campos epic/story/squad com
autocomplete + botão de download), `contextPackUrl` em `api.ts`.

## Scope boundaries

Não gera embeddings/indexação vetorial — o bundle é Markdown puro, quem faz
RAG com ele é o agente externo. Não envia o bundle automaticamente para
nenhum serviço — é sempre um download manual pelo usuário.

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
