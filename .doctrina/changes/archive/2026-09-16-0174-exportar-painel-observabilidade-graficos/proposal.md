# Change 0174-exportar-painel-observabilidade-graficos — exportar o painel de observabilidade e os graficos dos sinais

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** product
- **Affects specs:** ci-automation

## Why

exportar o painel de observabilidade e os graficos dos sinais

## What

- `backend/arbites/export_obs.py` (novo): `sinais_csv`, `painel_markdown` e
  `painel_pdf`. Os gráficos do PDF são desenhados com as primitivas do fpdf2
  — linha da série, ponto azul/vermelho conforme a execução, meta tracejada —
  e não capturados da tela.
- `backend/arbites/api.py`: `GET /ci/observability/export?format=pdf|csv|md&days=N`,
  no mesmo padrão de `/metrics/traceability/export` e `/todos/export`.
- `frontend/src/components/Observability.tsx` + `api.ts`: três links de
  download no cabeçalho, ao lado do período e de "Buscar execuções".

## Scope boundaries

- Os anexos do run (prints, logs) não entram no PDF: o documento é o painel,
  não o arquivo do run — que já é acessível pela descida e pesa MB por peça.
- Sem agendamento de envio: exportar é uma ação de quem está olhando.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Auditoria do caminho do dado com 28 runs mock ingeridos pela ingestão
      REAL (cliente GitHub falso devolvendo .zip com `arbites.json`): 28
      arquivos em `ci/`, 84 anexos, 4 sinais, 2 cenários instáveis.
- [x] Download dos três formatos exercitado no navegador, com o arquivo
      chegando nomeado pelo período; PDF renderizado e conferido.

## Open questions

Nenhuma.
