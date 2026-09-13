# Tasks — Change 0115-autoria-resultado-execucao-vem

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Remover `who` de `ResultStatusIn`, `StepStatusIn` e `DefectLinkIn`, e do form de evidência; recusar o campo com 422 em vez de ignorá-lo.
- [x] Passar `author_of(request)` nas quatro rotas de escrita em resultado.
- [x] `backend/tests/test_authorship_executions.py`: autoria da sessão sem `who` no corpo, recusa da autoria forjada e duas contas no mesmo caso.
- [x] Ajustar os clientes que ainda mandam `who` (frontend e testes existentes).

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0115-autoria-resultado-execucao-vem/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
