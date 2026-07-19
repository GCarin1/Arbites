# Change 0077-memoria-do-projeto-agrupar-timeline-por-dia — memoria do projeto: agrupar timeline por dia colapsavel e filtro de periodo ano/mes com filtro de data no backend

- **Status:** applied
- **Applied:** 2026-07-19
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** project-memory

## Why

A linha do tempo da Memória do Projeto cresce indefinidamente e hoje é uma
lista plana de até 100 eventos, com filtro só por tipo. Sem recorte por
data nem agrupamento, ela fica impraticável de navegar num projeto maduro —
o usuário não consegue "ir até um ano" nem colapsar o que não interessa.

## What

- **Backend (`project_memory.timeline`)** ganha filtro de data
  `date_from`/`date_to` (inclusivo, comparando o prefixo `YYYY-MM-DD` de
  `at`), aplicado a TODAS as fontes (requirement/testcase/defect/lesson/
  decision/agent/result) antes do corte por `limit`.
- **Backend** ganha `timeline_years(conn, kinds)` — anos DISTINTOS com
  eventos (UNION sobre as colunas de data das mesmas fontes), para popular o
  seletor de ano com dados reais, não um range chutado.
- **API** — `GET /memory/timeline` aceita `date_from`/`date_to`; novo
  `GET /memory/timeline/years?kinds=` devolve os anos disponíveis.
- **Frontend (`Memory.tsx`)** — controles combináveis no topo (Ano · Mês ·
  tipos · busca textual); eventos agrupados por dia em cabeçalhos
  colapsáveis (data + contagem); dias mais recentes expandidos, antigos
  colapsados. A busca é client-side sobre id/título/resumo dos eventos já
  carregados; Ano/Mês viram `date_from`/`date_to` na chamada. Segue o
  design system (skill `design-system-canonico`).

## Scope boundaries

- Não altera as fontes/derivação dos eventos (a timeline continua 100%
  derivada; nada editável) — só recorte e apresentação.
- Sem presets de filtro salvos (decisão do usuário: controles combináveis
  bastam) — nada persistido em localStorage/workspace.
- Sem paginação por cursor; o `limit` (cap 200) permanece o teto por
  janela, agora dentro do período selecionado.
- Não toca no recap injetado na IA (`recent_recap`).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] `timeline(date_from, date_to)` recorta por período em todas as fontes; `timeline_years` lista os anos com eventos — `backend/tests/test_project_memory.py`.
- [x] `npm run build` limpo; a aba agrupa por dia colapsável e os filtros Ano/Mês/tipos/busca combinam (revisão visual).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
