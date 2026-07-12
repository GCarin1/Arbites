# Spec Delta — capability: project-memory

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/project-memory/spec.md`

Note: o conteúdo completo já foi escrito diretamente em
`.doctrina/specs/project-memory/spec.md` via `doctrina spec new
project-memory` + edição manual (mesmo padrão usado nas changes
0053/0055/0056/0057, capabilities `decisions`/`audit`/`context-pack`/
`risk-map`) — este delta documenta o que entrou, `Operation: MODIFIED`
porque o arquivo alvo já existe (criado pelo scaffold) em vez de `ADDED`.

---

Nova capability `project-memory` (Memória Histórica do Projeto e para a
IA):

- `GET /memory/timeline?kinds=&limit=` cruza `requirement`/`defect`/
  `lesson`/`decision`/`agent` num feed cronológico único, mais recente
  primeiro.
- Novo tipo de artefato `agent_events` (persistido em `agent_log/`,
  prefixo `AGT`), registrado após `generate-testcases`/`review`/
  `negative-cases` completarem com sucesso.
- Um defeito com `root_cause` gera um evento `lesson` ADEMAIS do evento
  `defect` (os dois convivem).
- `_with_project_recap` injeta decisões aceitas + lições recentes no
  prompt de `generate-testcases` e `review`, empilhado sobre a memória de
  longo prazo do Perfil (`_with_memory`) — sem bloco quando não há
  decisão/lição.

6 critérios de aceitação, todos `[verified]` — ver
`backend/tests/test_project_memory.py` (11 testes).
