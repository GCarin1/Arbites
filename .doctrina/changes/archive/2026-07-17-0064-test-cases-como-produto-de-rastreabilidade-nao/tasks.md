# Tasks — Change 0064-test-cases-como-produto-de-rastreabilidade-nao

- [x] Auditar `GET /testcases`: já tinha story/status/tag/type/folder/
      squad/q; faltava só `priority` — adicionado. `GET /defects` ganhou
      `testcase` (defeitos vinculados p/ o painel).
- [x] Busca fixa no topo da árvore + filtros combinados (status/prioridade/
      tipo/tag) — server-side via `GET /testcases` (debounced), a árvore
      exibe só os IDs que casaram (fonte única).
- [x] Contagem por pasta: `casaram/total` com filtro ativo; pastas sem match
      ocultas; empty state instrutivo quando nada casa.
- [x] Painel lateral (`TcDetailPanel`): clique seleciona (linha destacada),
      mostra status/tipo/prioridade/story/squad/tags + defeitos vinculados;
      ações rápidas: mudar status (PUT parcial + toast), copiar ID, abrir
      editor. Duplo clique abre o editor direto.
- [x] Testes: `test_priority_filter_and_combined_filters` +
      `test_defects_filter_by_testcase` (14/14 no arquivo).
- [x] `npm run build` limpo + smoke real (filtro combinado e
      `defects?testcase=` devolvendo os IDs certos via API).
- [x] Spec testcases: EARS + critério #9; versão 0.5.0 → 0.6.0.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-07-17-0064-test-cases-como-produto-de-rastreabilidade-nao/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
