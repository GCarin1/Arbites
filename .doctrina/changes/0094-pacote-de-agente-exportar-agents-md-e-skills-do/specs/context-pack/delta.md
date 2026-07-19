# Delta — context-pack (change 0094)

**Operation:** MODIFIED

Delta prose (merge manual na spec ao implementar, padrão do repo).

## MODIFIED — Requirements (EARS)

- The system shall expor `GET /agent-pack` (mesmos filtros de escopo
  obrigatório do context-pack) devolvendo um ZIP com `AGENTS.md`
  (convenções derivadas das decisões aceitas + visão do escopo),
  `skills/*.md` (lições de defeito com causa raiz estruturadas como
  when/procedure/anti-pattern) e `specs/*.md` (critérios EARS + CTs BDD),
  com `layout=agents-md|claude` controlando os caminhos; a UI shall
  oferecer o download na sub-aba Context Pack. [unverified]

## Acceptance criteria (append — numeração final no merge)

- [unverified] O ZIP traz AGENTS.md/skills/specs coerentes com o escopo
  nos dois layouts, com 422 sem escopo — verified by
  `backend/tests/test_agent_pack.py` + build + revisão visual.
