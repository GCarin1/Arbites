# Tasks — Change 0079-context-pack-escopo-com-pickers-que-listam-itens

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `context_pack.build`: retorna `{markdown, counts, bytes}`; toggles `include_testcases`/`include_defects`/`include_decisions`/`include_last_result`; decisões incluídas em qualquer escopo (squad → do squad; senão ADRs aceitas); último resultado por CT via `results`.
- [x] API `GET /context-pack`: params `testcases`/`defects`/`decisions`/`last_result`/`format`; `format=json` → `{scope, counts, bytes, markdown}`; mantém 422 `scope_required` e o attachment `md`.
- [x] `api.ts`: `contextPack(params)` (json) + helper de download client-side; manter `contextPackUrl` para o link direto.
- [x] `AiAssist.tsx` ContextPackCard: 3 campos com `<datalist>` listando epics/stories/squads (filtra ao digitar), toggles de seção + último resultado, hint de escopo obrigatório (sem "(opcional)").
- [x] ContextPackCard: preview com contagens + tamanho, `<pre>` do markdown, botões Copiar (clipboard + toast) e Baixar .md (blob). Segue o design system.
- [x] Testes: `test_context_pack.py` para `format=json`/counts, toggles, decisões sem squad, último resultado; `npm run build` limpo.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-19-0079-context-pack-escopo-com-pickers-que-listam-itens/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
