# Spec Delta — capability: context-pack

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/context-pack/spec.md`

Note: o conteúdo completo já foi escrito diretamente em
`.doctrina/specs/context-pack/spec.md` via `doctrina spec new context-pack`
+ edição manual (mesmo padrão usado nas changes 0053/0055, capabilities
`decisions`/`audit`) — este delta documenta o que entrou, `Operation:
MODIFIED` porque o arquivo alvo já existe (criado pelo scaffold) em vez de
`ADDED`.

---

Nova capability `context-pack` (Context Pack para agentes de IA):

- `GET /context-pack?epic=&story=&squad=` — ao menos um filtro obrigatório
  (422 `scope_required` sem nenhum).
- Bundle Markdown único com requisitos (epic/stories), CTs e defeitos do
  escopo, cada um com o corpo completo lido do disco.
- Defeitos incluem causa raiz/correção quando registradas (liga com
  Lições Aprendidas, capability `defects`).
- `squad=` inclui as decisões arquiteturais daquele squad.
- `story=` restringe a uma única story mesmo dentro de um epic maior;
  `epic=` sem `story=` inclui todas as stories do epic.
- Escopo válido sem achados devolve nota explícita, não erro.
- Download via `Content-Disposition: attachment; filename="context-pack.md"`.

5 critérios de aceitação, todos `[verified]` — ver
`backend/tests/test_context_pack.py` (6 testes).
