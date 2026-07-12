# Tasks — Change 0053

- [x] `workspace.py`: `SUBDIRS` ganha `decisions/`; `DEFAULT_CONFIG.id_prefixes` ganha `decision: DEC`
      (backward-compatible: `id_prefixes()` faz merge sobre o default, workspaces existentes
      herdam sem migração; `ws.ensure()` roda em todo startup e cria a pasta faltante).
- [x] `indexer.py`: tabela `decisions`; `_insert_decision`; wired em `reindex_full`/`reindex_file`/
      `_find_id` (detecção de ID duplicado cross-capability).
- [x] `api.py`: `DecisionIn`/`DecisionUpdate`; `DEFAULT_DECISION_BODY`; CRUD completo
      (`GET/POST /decisions`, `GET/PUT/DELETE /decisions/{id}`); `decision` em `/search` e em
      `_resolve_link` (links de Afazeres também podem apontar pra uma decisão).
- [x] Bug corrigido no processo: `DecisionIn.body` tinha default `""` em vez de `None` — o check
      `payload.body if payload.body is not None else DEFAULT_DECISION_BODY` nunca caía no
      template (string vazia não é `None`). Corrigido pro mesmo padrão de `TestcaseIn.body`.
- [x] Frontend: `Decision` type; `api.ts` (decisions/decision/create/update/delete); `Decisions.tsx`
      (lista estilo cards de Afazeres, filtro de status, modal com Contexto/Decisão/Consequências
      via MentionTextarea, `supersedes` via SingleRefInput).
- [x] `App.tsx`: nova aba "Decisões"; `navigateTo` ganha o ramo `DEC-XXXX`.
- [x] Testes (template padrão, filtros, CRUD completo com lixeira, supersedes, busca/reindex)
      + suíte verde (165) + build.
- [x] Smoke HTTP real (criar → listar → buscar → GET individual com template).

## Closing steps

- [x] Apply: spec nova escrita em `.doctrina/specs/decisions/spec.md` (via `doctrina spec new`).
- [x] Archive.
- [x] Update index.json.
