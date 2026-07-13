# Tasks — Change 0064-test-cases-como-produto-de-rastreabilidade-nao

- [ ] Auditar `GET /testcases`: quais filtros já existem (status? tag?
      prioridade? tipo? story?) e completar os params que faltarem + testes.
- [ ] Busca fixa no topo da árvore (filtra por ID/título, expande e realça
      pastas com match).
- [ ] Barra de filtros combinados (status/tag/prioridade/tipo/story) na UI.
- [ ] Contagem por pasta na árvore (total + filtrada quando há filtro).
- [ ] Painel lateral de detalhes do CT selecionado (status, story, tags,
      últimos resultados, defeitos ligados) sem sair da árvore.
- [ ] Ações rápidas no painel: mudar status (PUT existente), abrir editor,
      copiar ID.
- [ ] Badges de status na linha do CT (canônico da 0060 se disponível).
- [ ] Suíte completa verde + `npm run build` limpo + smoke test.
- [ ] Atualizar spec testcases: critérios novos → verified; bump minor.

## Closing steps

- [ ] Apply the change: merge each delta into the corresponding spec.
- [ ] Archive the change folder to `.doctrina/changes/archive/2026-07-13-0064-test-cases-como-produto-de-rastreabilidade-nao/`.
- [ ] Update `.doctrina/index.json` with new or modified artifacts.
