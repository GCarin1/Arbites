# Tasks — Change 0169-tela-troca-senha-obrigatoria

<!--
Each task is a single checkable item. Keep tasks small (under a few hours
of work). The change is done when every box is checked, including the
three closing steps at the bottom.
-->

- [x] Reproduzir o estado relatado no navegador e isolar a causa.
- [x] `key` por fase no `<Login>`, para a tela de troca existir.
- [x] A fase de troca roteia por `must_change_password` em vez de confiar no login.
- [x] Canal para `password_change_required`, que resgata a sessão já montada.
- [x] Cartão Senha no Perfil, para trocar fora da obrigação.
- [x] Testes fixando o contrato que a tela consome.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-15-0169-tela-troca-senha-obrigatoria/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
