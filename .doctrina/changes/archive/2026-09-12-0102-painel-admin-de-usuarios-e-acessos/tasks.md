# Tasks — Change 0102-painel-admin-de-usuarios-e-acessos

- [x] `auth.py`: listagem de contas com contagem de sessões abertas por conta.
- [x] `api.py`: `GET /admin/users` e as ações aprovar, recusar, ativar, desativar, papel, senha temporária e encerrar sessões.
- [x] `api.py`: recusa de auto-rebaixamento (`self_demotion`) e reaproveitamento da trava do último admin.
- [x] `api.py`: `GET /admin/access-log` paginado e `GET /admin/overview`.
- [x] `api.py`: incluir o prefixo `/admin/` inteiro na tabela de superfícies governadas.
- [x] `frontend`: `Admin.tsx` com as abas Usuários, Acessos e Sistema.
- [x] `frontend`: fila de pendentes destacada, com o papel escolhido na própria aprovação.
- [x] `frontend`: aba Administração no menu, visível apenas ao papel admin.
- [x] `backend/tests/test_admin_panel.py` cobrindo os 7 critérios.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0102-painel-admin-de-usuarios-e-acessos/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
