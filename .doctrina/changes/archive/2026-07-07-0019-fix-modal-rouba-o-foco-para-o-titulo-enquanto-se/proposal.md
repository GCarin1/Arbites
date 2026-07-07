# Change 0019-fix-modal-rouba-o-foco-para-o-titulo-enquanto-se — fix: modal rouba o foco para o titulo enquanto se digita em outro campo (efeito de foco re-disparava com nova identidade de onClose no re-render); e robustez do autocomplete (strip de @/! no termo de busca). O 404 em /search era backend desatualizado (endpoint novo da change anterior) — exige restart do uvicorn

- **Status:** applied
- **Applied:** 2026-07-07
- **Date:** 2026-07-07
- **Owner:**
- **Affects specs:** (none — chore)

## Why

fix: modal rouba o foco para o titulo enquanto se digita em outro campo (efeito de foco re-disparava com nova identidade de onClose no re-render); e robustez do autocomplete (strip de @/! no termo de busca). O 404 em /search era backend desatualizado (endpoint novo da change anterior) — exige restart do uvicorn

## What

- **Modal.tsx** — o efeito que dá foco inicial e trava o scroll passou a rodar
  **só no mount** (deps `[]`); antes tinha `[onClose, initialFocus]` nas deps, e
  como os pais passam um `onClose` recriado a cada render (e o App re-renderiza a
  cada 5s pelo refresh), o efeito re-disparava e **re-focava o título** no meio da
  digitação. O `onClose` do Esc agora é lido por uma ref, fora das deps.
- **Autocomplete.tsx** — `useSuggestions` normaliza o termo (remove `@`/`!`/espaços
  à frente): "@CT-0001" busca "CT-0001" e "@" sozinho não dispara requisição.
- **metrics.py** — bug de fuso capturado pelo `doctrina verify` deste fix:
  `defects_report` calculava aging com `datetime.now(timezone.utc).date()`, mas o
  `opened` do defeito é carimbado com `date.today()` (local). À noite em fusos
  atrás do UTC (Brasil, 21h = 00h UTC do dia seguinte) as datas divergiam e o
  `age_days` saía 1 em vez de 0. Passou a usar `date.today()` (local),
  consistente com o carimbo — coberto por
  `test_defects.py::test_defects_report_aging_severity_and_squad`.

## Diagnóstico do 404 em /search

Reproduzido em código: `GET /api/v1/search?q=CT-0001` → 200 e acha o CT;
`q=@CT-0001` → 200 com `[]` (ids não contêm `@`). Ou seja, a rota existe e
funciona (coberta por `test_todos.py::test_search_entities_for_autocomplete`).
O 404 observado ao vivo é **backend desatualizado**: `/search` e `/todos/export`
entraram na change anterior (0018); o processo uvicorn em execução é anterior a
ela. **Correção operacional: reiniciar o backend.** O front foi endurecido para
não mandar `@` cru como filtro.

## Scope boundaries

- Correção de bug de UI + robustez; sem mudança de comportamento de spec.
- Não altera a rota `/search` (já correta); o 404 é ambiente (restart).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (pytest 88 + build do frontend).
- [x] `/search` confirmado 200 em código (o 404 ao vivo é backend desatualizado → restart).
- [x] Modal: foco só no mount; digitar em outro campo não volta ao título.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
