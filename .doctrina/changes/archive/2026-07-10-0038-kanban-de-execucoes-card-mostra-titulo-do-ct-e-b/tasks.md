# Tasks — Change 0038

- [x] Backend: `exec_ops.unlink_defect`; rotas `POST/DELETE .../results/{ct}/defects[/{defect_id}]`; `DefectLinkIn`.
- [x] Frontend: card do Kanban com título do CT + barra de progresso (% de passos passed).
- [x] Frontend: `ResultPanel` passa a abrir dentro de `Modal` (título + X), não mais inline.
- [x] Frontend: seção "Defeitos" ganha vincular defeito existente (picker) + desvincular por item.
- [x] `Modal`: pilha de modais abertos — Esc fecha só o do topo (necessário para "Criar defeito" aninhado dentro do modal de resultado).
- [x] Testes backend (link idempotente, unlink, 404 defeito inexistente, 409 execution fechada) + suíte verde + build.
- [x] Smoke test HTTP end-to-end contra servidor real (create CT/execution, marcar step, criar/vincular/desvincular defeito, 404/409).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder.
- [x] Update `.doctrina/index.json`.
