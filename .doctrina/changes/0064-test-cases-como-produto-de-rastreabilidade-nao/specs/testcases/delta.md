# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

Repositório de CTs como produto de rastreabilidade — requisitos a
acrescentar (todos [unverified] até implementar):

### Ubiquitous

- The system shall manter uma busca fixa no topo do repositório de CTs que
  filtra a árvore por ID/título, expandindo e realçando as pastas com
  resultado.
- The system shall oferecer filtros combinados por status, tag, prioridade,
  tipo (manual/automated/hybrid) e story vinculada, aplicados à árvore.
- The system shall exibir a contagem de CTs por pasta (total e, quando há
  filtro ativo, a contagem filtrada).
- The system shall abrir um painel lateral de detalhes ao selecionar um CT
  (status, story, tags, últimos resultados, defeitos ligados) sem sair da
  árvore, com ações rápidas (mudar status, abrir editor completo).

### Unwanted-behavior (must-not)

- The system shall not exigir navegar para a tela de edição completa para
  consultar detalhes ou mudar o status de um CT.

### Acceptance criteria (a acrescentar)

- [unverified] Buscar por ID/título filtra a árvore e realça os matches;
  filtros de status/tag/prioridade/tipo/story combinam entre si — verified
  by teste de API (params de filtro) + revisão visual documentada.
- [unverified] Selecionar um CT abre o painel lateral com detalhes e
  permite mudar status sem abrir o editor — verified by revisão visual
  documentada + teste de API do update de status.

### Maturity → MVP (acrescentar)

- Busca fixa + filtros combinados + contagem por pasta + painel lateral de
  detalhes com ações rápidas.
