# Change 0042-arrastar-pastas-para-dentro-de-outras-pastas-em — arrastar pastas para dentro de outras pastas em Test cases: nova rota POST /testcases/folders/move (reindexa recursivamente, guarda contra path traversal e mover pasta para dentro dela mesma/descendente); pasta vira draggable no repo; se contiver CTs (recursivo), abre modal de confirmacao antes de mover pois os casos de teste vao junto

- **Status:** proposed
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** testcases

## Why

arrastar pastas para dentro de outras pastas em Test cases: nova rota POST /testcases/folders/move (reindexa recursivamente, guarda contra path traversal e mover pasta para dentro dela mesma/descendente); pasta vira draggable no repo; se contiver CTs (recursivo), abre modal de confirmacao antes de mover pois os casos de teste vao junto

## What

- **backend/arbites/api.py** — `FolderMoveIn`; `POST /testcases/folders/move`
  (rota estática, adicionada ANTES de `/testcases/{entity_id}` — mesma
  disciplina das demais rotas de pasta). Renomeia o diretório inteiro
  (`Path.rename`), reindexa os `.md` afetados no caminho antigo (remove) e no
  novo (indexa). Guardas: 422 traversal/self-descendant, 409 destino ocupado,
  no-op se já está no destino.
- **frontend/src/components/TcRepository.tsx** — pastas viram `draggable`;
  `DragState` (`ct` | `folder`) substitui o antigo `dragId` só-de-CT;
  `isDescendantOrSelf` bloqueia visualmente soltar uma pasta nela mesma/numa
  descendente. Se a pasta arrastada contém CTs (recursivo, via `countAll`
  já existente), abre `ConfirmModal` antes de mover, avisando quantos CTs
  vão junto.
- **frontend/src/api.ts** — `moveTcFolder(path, dest)`.
- **testcases spec** MODIFIED (delta) + critério [verified] #8.

## Bug de concorrência exposto (não introduzido, mas corrigido aqui)

Testar esta feature contra um servidor real (não só `TestClient`, que roda
com `watch=False`) revelou um 500 genuíno: o watcher (thread + conexão
SQLite próprias) e o handler HTTP (outra conexão) já podiam colidir em
"database is locked" — só que operações de um arquivo só raramente
disparavam a corrida. Mover uma pasta gera uma rajada de eventos do watcher
(um por `.md` afetado) que colide de verdade com o loop de reindex do
próprio handler. Corrigido na raiz: `backend/arbites/indexer.py`,
`reindex_file` agora retenta (com `rollback()` entre tentativas) em vez de
deixar a exceção subir — beneficia TODO chamador (watcher e handlers), não
só esta rota nova.

## Scope boundaries

- Só `testcases/` (Requirements usa hierarquia epic→story, não pastas
  livres — fora de escopo aqui).
- A correção de concorrência é mínima (retry local) — não redesenha a
  arquitetura de conexão única compartilhada por thread.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (128 testes backend + build frontend).
- [x] Critério #8 do testcases cita `backend/tests/test_tc_repository.py`; retry de
      concorrência coberto por `backend/tests/test_indexing.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
