# Tasks — Change 0126-escala-espacamento-valores-abaixo

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Degraus `--s0` (4px) e `--s1h` (12px) na escala, e os valores mágicos mais repetidos trocados por eles.
- [x] Três densidades por `data-density` na raiz, alterando respiro de linha e altura de controle.
- [x] Aplicar o respiro nas superfícies de linha: tabela, árvore do repositório, navegação, cards do quadro, listas.
- [x] Seletor de densidade no Perfil, persistido no navegador e aplicado na carga da página.
- [x] Garantir que a compacta não vença o alvo de toque de 44px sob ponteiro grosseiro.
- [x] Verificar no navegador: contar linhas visíveis nas três densidades e conferir que nada transborda.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-13-0126-escala-espacamento-valores-abaixo/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
