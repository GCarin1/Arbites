# Change 0081-lixeira-listar-e-restaurar-itens-da-trash-pela — lixeira: listar e restaurar itens da trash pela UI

- **Status:** proposed
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** workspace-core

## Why

Todo delete move para `.arbites/trash/` (nunca apaga), mas não há UI:
"restaurar" hoje é mexer no filesystem na mão. A rede de segurança existe e
não aparece.

## What

- Backend: `GET /trash` (itens com nome original, tipo inferido do
  prefixo/pasta, data de moção), `POST /trash/{name}/restore` (volta ao
  caminho original registrado ou à pasta raiz do tipo + reindex) e
  `DELETE /trash` (esvaziar, com confirmação).
- `ws.trash()` passa a registrar o caminho de origem (sidecar
  `.origin` ou nome codificado) para restore fiel.
- Frontend: seção "Lixeira" (na aba Problemas ou tela própria) com lista,
  Restaurar por item e Esvaziar lixeira (ConfirmModal + toast).

## Scope boundaries

- Sem retenção automática/expiração (esvaziar é manual).
- Restore não resolve conflito de ID duplicado além de sufixar o arquivo
  (o reindex acusa duplicata como warning, comportamento já existente).

## Verification

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Deletar CT → aparece em `GET /trash`; restore devolve o arquivo ao lugar e o item volta ao índice; esvaziar limpa — `backend/tests/test_workspace.py` (ou novo `test_trash.py`).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
