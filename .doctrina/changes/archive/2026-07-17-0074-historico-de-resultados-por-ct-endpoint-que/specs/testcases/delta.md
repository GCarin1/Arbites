# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

Histórico de resultados por CT ([unverified] até implementar):

### Ubiquitous
- The system shall expor `GET /testcases/{tc_id}/results` com os resultados
  passados do CT (execution_id, status, executed_at, duration), mais
  recente primeiro, derivado da tabela `results`.
- The system shall exibir esse histórico no painel lateral do repositório
  e no editor do CT (sequência de status-dots + lista), respondendo "já
  passou no passado?".

### Acceptance criteria (a acrescentar)
- [unverified] CT executado em 2 executions mostra os 2 resultados na
  ordem certa via endpoint; painel/editor exibem — verified by teste de
  API + revisão visual.
