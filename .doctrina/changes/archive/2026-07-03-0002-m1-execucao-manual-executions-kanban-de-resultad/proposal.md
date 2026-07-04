# Change 0002-m1-execucao-manual-executions-kanban-de-resultad — M1 - execucao manual: executions, kanban de resultados, steps marcaveis, evidencias com hash, historico, defeitos minimos, fechamento

- **Status:** proposed
- **Date:** 2026-07-03
- **Owner:** Gcarini
- **Affects specs:** executions, defects

## Why

M1 é o segundo passo da ordem de entrega (product.md): com o M0 verificado,
a plataforma precisa executar uma regressão manual completa sem tocar em
outro sistema. Critério de pronto = SC2: ~20 CTs executados, com evidências
anexadas (hash SHA-256) e um defeito vinculado.

## What

- `backend/arbites/executions.py` — ciclo de execution (`execution.json`
  em `executions/<ano>/EXEC-XXXX/`): criação com snapshot dos steps dos
  CTs, três máquinas de estado independentes (ADR 0005), history de
  eventos, evidências hasheadas, fechamento.
- Indexer/watcher estendidos: scan de `executions/**/execution.json` para
  as tabelas `executions`, `results`, `evidences`; incremental via watcher.
- API M1 completa (contrato http-api): `GET/POST /executions`,
  `GET/PATCH /executions/{id}`, `POST .../results/{ct}/status`,
  `POST .../results/{ct}/steps/{n}`, `POST/DELETE .../results/{ct}/evidences`,
  `POST .../close`, `GET/POST /defects`, `PUT /defects/{id}`.
- Frontend: aba Execuções — lista, criação (form com seleção de CTs),
  tela de execução com Kanban (drag nativo), painel do CT (steps
  marcáveis, upload de evidência, comentário, criação de defeito),
  fechamento.
- Testes: `backend/tests/test_executions.py`,
  `test_executions_e2e.py` (SC2), `test_defects.py`.

## Scope boundaries

- Sem runs automatizados (`origin` local_run/github_actions são M3/M4; o
  campo existe, o fluxo não).
- Sem métricas/matriz (M1.5) — o vínculo defeito→story só aparece na
  matriz no M1.5; aqui o defeito é criado e vinculado ao resultado.
- Sem cadastro de sprint/ambiente (texto livre, ADR 0010).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
