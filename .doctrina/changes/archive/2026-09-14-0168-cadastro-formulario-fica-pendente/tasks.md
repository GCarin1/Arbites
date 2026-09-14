# Tasks — Change 0168-cadastro-formulario-fica-pendente

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] `auth.py`: helpers que decidem quando um cadastro nasce dono.
- [x] `POST /auth/register` cria `admin`/`active` no caso do dono e informa qual dos dois caminhos aconteceu.
- [x] `GET /auth/me` revela `no_admin` e `owner_declared` para quem não tem sessão.
- [x] Tela de login avisa antes do cadastro e ensina a saída que serve.
- [x] Testes cobrindo as duas saídas, a comparação sem caixa e o limite (com admin ativo, ninguém mais nasce dono).
- [x] ADR 0018 aceito.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-14-0168-cadastro-formulario-fica-pendente/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
