# Change 0096-resumo-de-falha-pos-run-pela-ia-com-defeito — resumo de falha pos-run pela IA com defeito draft

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** ai-assist

## Why

Run falhou → o QA lê log cru. A IA já está plugada; falta o caso de uso
mais óbvio de automação: resumir a falha e pré-preencher o defeito.

## What

- Backend: `POST /ai/analyze-run/{exec_id}` — junta tail do log + CTs
  failed/blocked da execution → resumo, causa provável e um DRAFT de
  defeito (título/severidade sugerida/descrição) — preview, nada gravado.
- UI: botão "Analisar falha com IA" na execution local_run com falha (e no
  histórico da Automação); aceite do draft cria o defeito já vinculado ao
  CT/execution.

## Scope boundaries

- Análise é sugestiva (preview obrigatório, como toda IA no produto).
- Sem análise automática pós-run (ação explícita do usuário).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Endpoint devolve resumo+draft de defeito para execution com falha; aceite cria defeito vinculado — `backend/tests/test_ai_analyze_run.py` (MockTransport).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
