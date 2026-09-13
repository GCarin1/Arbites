# Change 0102-painel-admin-de-usuarios-e-acessos — Painel admin de usuarios e acessos

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** runtime (confident; signals: log) — opened anyway (--force)
- **Affects specs:** admin

## Why

Painel administrativo no frontend, visivel apenas para o papel admin, com duas abas iniciais: Usuarios (lista com papel, status, ultimo login e data de criacao; acoes de aprovar ou recusar cadastro pendente, ativar e desativar, trocar papel, forcar reset de senha e encerrar sessoes ativas; nunca deletar, para preservar a autoria historica) e Acessos (fila de cadastros pendentes mais o log de autenticacao com login bem sucedido, login falho, IP real lido de CF-Connecting-IP, user-agent e data). Inclui a aba Sistema com estado do indice, tamanho da lixeira, versao e os kill switches.

## What

- Capability nova `admin` (`.doctrina/specs/admin/spec.md`).
- `product.md`: critério SC16.
- `backend/arbites/api.py`: rotas `/admin/users*`, `/admin/access-log`,
  `/admin/overview`.
- `backend/arbites/auth.py`: contagem de sessões por conta na listagem.
- `frontend/src/components/Admin.tsx` (novo) + aba Administração visível só
  ao papel `admin`.
- `backend/tests/test_admin_panel.py`.

## Scope boundaries

- Não apaga conta, em nenhuma rota: desativar preserva a autoria histórica.
- Não edita artefato de QA — o painel governa acesso, não conteúdo.
- A aba Atividade (quem criou/editou/apagou o quê) é o 0103; aqui a aba
  Acessos cobre só autenticação.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `python -m pytest backend/tests -q` passa com o novo
      `backend/tests/test_admin_panel.py`.
- [x] `npm --prefix frontend run build` passa com a aba Administração.
- [x] Os 7 acceptance criteria de `admin` estão `[verified]`.
- [x] Nenhuma rota do painel aceita papel diferente de `admin`, provado por
      varredura das rotas `/admin/`.

## Open questions

Nenhuma.
