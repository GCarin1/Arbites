# Spec Delta — capability: audit

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/audit/spec.md`

Note: o conteúdo completo já foi escrito diretamente em
`.doctrina/specs/audit/spec.md` via `doctrina spec new audit` + edição
manual (mesmo padrão usado na change 0053, capability `decisions`) — este
delta documenta o que entrou, `Operation: MODIFIED` porque o arquivo alvo já
existe (criado pelo scaffold) em vez de `ADDED`.

---

Nova capability `audit` (Agente Auditor):

- `POST /audit/run`, `GET /audit/latest` (lazy auto-rerun após
  `audit.auto_interval_hours`, default 24h), `GET /audit/history`,
  `GET /audit/{id}`.
- 4 categorias de achado: `indexing` (warnings existentes), `coverage`
  (stories sem CT), `defects` (aging + causa raiz ausente/presente),
  `automation` (repos quebrados há N dias).
- Cada achado com categoria/código/severidade(`bad`|`warn`|`info`)/
  mensagem/ref, ordenados pior-primeiro.
- Persistência como Markdown com frontmatter em `audits/AUD-NNNN.md`
  (mesmo padrão de `decisions/`), tabela `audits` no índice SQLite
  descartável.
- Limiares configuráveis em `arbites.yaml` (`audit.defect_aging_days`,
  `audit.broken_automation_days`, `audit.auto_interval_hours`).
- Sem daemon: toda execução é síncrona e disparada por uma chamada HTTP.

5 critérios de aceitação, todos `[verified]` — ver
`backend/tests/test_audit.py` (16 testes).
