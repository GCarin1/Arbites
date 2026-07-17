# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: 3ª e última slice. Landou → critério #4 → verified; Implementation da
capability de `partial` para `verified` (as 3 slices completas).

---

O que landou (orientação & navegação):

### Ubiquitous

- **Busca global (flagship):** `CommandPalette`
  (`frontend/src/components/CommandPalette.tsx`), atalho Ctrl/Cmd+K de
  qualquer tela (listener global no `App.tsx`). Busca qualquer artefato via
  `GET /search` (sem backend novo — mesmo endpoint do autocomplete) e navega
  via `navigateTo`; inclui ações rápidas (novo CT, nova execução, reindex).
  Trigger visível no header ("Buscar… Ctrl K").
- **Breadcrumbs:** os back-bars das áreas profundas (execução, requisito,
  CT — criar/detalhe) mostram o caminho "Seção / ID", além do "← Voltar".
- **Telas grandes:** `.content-narrow` (max-width de leitura) aplicado onde
  a prosa/formulário estica (Profile); `.editor` já capava em 960px.

### Acceptance criteria

4. [verified] — ver spec (Ctrl+K de qualquer tela, breadcrumbs, largura de
   leitura; build limpo + smoke).

### Decisão / rollout

Breadcrumbs aplicados nos 4 back-bars principais e `.content-narrow` onde
mais pesa; o rollout às demais áreas profundas é incremental. A busca
global — o item de maior valor da slice — está completa e cobre "de
qualquer tela".
