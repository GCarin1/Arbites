# Tasks — Change 0113-tela-de-execucao-guiada-em-tres-paineis

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `frontend/src/components/ExecutionGuided.tsx`: três painéis (ciclos, casos do ciclo, caso ativo) sobre os endpoints que já existem.
- [x] Painel do caso ativo com passos marcáveis, evidência, comentário e resultado, sem modal.
- [x] Rodapé com a posição no ciclo, avanço para o próximo e o atalho "resultado e próximo".
- [x] Alternância Kanban ↔ guiado na aba de execuções, preservando a execução selecionada.
- [x] `backend/tests/test_executions_guided.py`: a sequência do modo guiado grava na mesma execution e respeita o ciclo fechado.
- [x] Estilos dos três painéis, responsivos ao colapso do painel do meio.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0113-tela-de-execucao-guiada-em-tres-paineis/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
