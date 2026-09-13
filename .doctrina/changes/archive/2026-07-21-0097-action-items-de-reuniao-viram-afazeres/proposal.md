# Change 0097-action-items-de-reuniao-viram-afazeres — action items de reuniao viram afazeres

- **Status:** applied
- **Applied:** 2026-07-21
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** meetings

## Why

A daily converte action items em todos; a reunião não — a transcrição
fica parada. Mesmo mecanismo, mesma UX, loop reunião→afazer fechado.

## What

- Extração de action items da reunião: determinística (linhas `- [ ]` na
  descrição/transcrição) + IA opcional (mesmo padrão da daily) — sempre
  preview com checkboxes.
- Aceite cria todos vinculados à reunião (link no todo, mesma convenção da
  daily).
- Na tela da reunião: seção "Action items" com o preview e o histórico dos
  já convertidos.

## Scope boundaries

- Sem IA, só a extração determinística funciona (aba 100% funcional sem
  provider, como a spec de meetings exige).
- Não re-extrai automaticamente ao editar a reunião (ação explícita).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Linhas `- [ ]` viram preview; aceite cria todos vinculados; sem provider o fluxo determinístico funciona — `backend/tests/test_meetings.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
