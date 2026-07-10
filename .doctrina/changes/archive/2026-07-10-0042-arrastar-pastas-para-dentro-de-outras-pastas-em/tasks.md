# Tasks — Change 0042

- [x] Backend: `FolderMoveIn`; `POST /testcases/folders/move` (rota estática antes de `/{entity_id}`).
- [x] Backend: reindexa caminhos antigos (remove) e novos (indexa) após `Path.rename` da pasta.
- [x] Backend: guardas — traversal, mover para si mesma/descendente (422), destino ocupado (409), no-op se já está lá.
- [x] Frontend: pasta vira `draggable`; `DragState` distingue CT vs pasta; `isDescendantOrSelf` bloqueia drop inválido.
- [x] Frontend: se a pasta arrastada contém CTs (recursivo via `countAll`), abre `ConfirmModal` antes de mover.
- [x] api.ts: `moveTcFolder`.
- [x] Bug pré-existente exposto por esta feature: `reindex_file` não tolerava a corrida entre a
      conexão do watcher (thread própria) e a do handler HTTP numa rajada de eventos (mover pasta
      com vários CTs) — corrigido com retry+rollback em `_reindex_file_once`, testado com watcher
      real (não só TestClient, que roda com watch=False).
- [x] Testes backend (move, cycle, conflict, no-op, traversal, retry-on-locked) + suíte verde + build.
- [x] Smoke HTTP contra servidor real com watcher ligado (3 CTs) — sem esse teste ao vivo o bug de
      concorrência não teria aparecido (pytest usa `watch=False`).

## Closing steps

- [x] Apply: merge delta na spec testcases.
- [x] Archive.
- [x] Update index.json.
