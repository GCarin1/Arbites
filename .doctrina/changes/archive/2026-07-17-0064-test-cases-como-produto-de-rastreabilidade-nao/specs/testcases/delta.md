# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

Repositório de CTs como produto de rastreabilidade — o que landou:

### Ubiquitous

- Filtros de `GET /testcases` completados com `priority` (agora:
  story/status/tag/type/priority/folder/squad/q, todos combináveis).
- `GET /defects` ganhou o filtro `testcase` (defeitos vinculados a um CT —
  fonte do painel lateral).
- Busca fixa no topo do repositório + filtros combinados
  (status/prioridade/tipo/tag) na UI — o filtro roda no SERVIDOR (mesmo
  endpoint), a árvore exibe só os IDs que casaram (fonte única, sem
  reimplementar filtro no cliente — ver skill
  fonte-do-preview-diverge-da-fonte-da-operacao).
- Contagem por pasta: `casaram/total` com filtro ativo; pastas sem match
  ocultas; empty state instrutivo quando nada casa.
- Painel lateral de detalhes (clique na linha): status/tipo/prioridade/
  story/squad/tags + defeitos vinculados, com ações rápidas — mudar status
  (PUT parcial + toast), copiar ID, abrir editor completo. Duplo clique na
  linha ainda abre o editor direto.

### Acceptance criteria

9. [verified] `priority` combinável + `GET /defects?testcase=` — verified by
   `backend/tests/test_testcases.py`
   (`test_priority_filter_and_combined_filters`,
   `test_defects_filter_by_testcase`).

Versão `0.5.0` → `0.6.0`.
