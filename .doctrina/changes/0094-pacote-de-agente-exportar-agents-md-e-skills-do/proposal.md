# Change 0094-pacote-de-agente-exportar-agents-md-e-skills-do — pacote de agente: exportar AGENTS.md e skills do escopo

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** context-pack

## Why

O Arbites acumula exatamente o que um agente de código precisa e nunca
tem: decisões aceitas, lições de defeitos reais, critérios EARS, casos BDD.
O Context Pack exporta um Markdown de chat; falta o formato REPOSITÓRIO —
AGENTS.md + skills prontos para colar no projeto.

## What

- Backend: `GET /agent-pack?epic|story|squad&layout=` gerando um ZIP
  (zipfile stdlib, StreamingResponse) com:
  `AGENTS.md` (visão do escopo, convenções = decisões aceitas, glossário
  dos artefatos), `skills/<slug>.md` (uma por lição de defeito com
  root_cause → when/procedure/anti-pattern), `specs/<story>.md` (critérios
  EARS + CTs BDD do escopo).
- `layout=agents-md` (padrão aberto, default) e `layout=claude`
  (`.claude/skills/...`) — mesmo conteúdo, caminhos diferentes.
- UI: na sub-aba Context Pack, seção "Pacote de Agente" com o mesmo
  seletor de escopo + escolha de layout + Baixar .zip.

## Scope boundaries

- Mesma fonte de dados do context-pack (traceability + decisions +
  defects) — nenhum dado novo.
- Sem push automático para repositório (o usuário baixa e commita).
- Conteúdo genérico/white-label (nunca citar organização).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] ZIP contém AGENTS.md + skills das lições + specs do escopo; layout=claude muda caminhos; escopo obrigatório (422) — novo `backend/tests/test_agent_pack.py`.
- [ ] UI baixa o zip — build + revisão visual.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
