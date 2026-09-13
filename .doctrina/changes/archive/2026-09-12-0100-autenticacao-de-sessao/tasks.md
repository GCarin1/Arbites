# Tasks — Change 0100-autenticacao-de-sessao

- [x] ADR 0011: contas e sessões em `.arbites/auth.db`, banco durável fora do índice descartável.
- [x] `product.md`: tirar autenticação do "Out of scope", registrar SC15 e o M14.
- [x] `backend/arbites/auth.py`: schema SQLite (`users`, `sessions`, `login_attempts`) e conexão durável separada da do índice.
- [x] `auth.py`: hash Argon2id, verificação, política de senha mínima de 12 caracteres.
- [x] `auth.py`: criar conta (`pending`/`viewer`), aprovar, recusar, desativar, trocar papel — com a trava do último admin.
- [x] `auth.py`: abrir sessão (id opaco de 256 bits, guardado em SHA-256), validar com expiração por inatividade e por idade, revogar por usuário.
- [x] `auth.py`: registrar tentativa de login e aplicar lockout de 5 falhas em 15 minutos, por conta e por IP.
- [x] `auth.py`: bootstrap do primeiro admin por `ARBITES_ADMIN_EMAIL`/`ARBITES_ADMIN_PASSWORD` com `must_change_password`.
- [x] `api.py`: rotas `POST /auth/register|login|logout|password` e `GET /auth/me`, com resposta de erro indistinguível no login.
- [x] `api.py`: middleware de gate 401 em toda a API, com allowlist do login/cadastro/estáticos e o desvio de `password_change_required`.
- [x] `api.py`: derivar IP real de `CF-Connecting-IP` → `X-Forwarded-For` → socket.
- [x] `api.py`: escape hatch `ARBITES_AUTH=off` com aviso alto no log de inicialização.
- [x] `frontend`: tela de login com cadastro, estado "aguardando aprovação" e troca de senha obrigatória.
- [x] `frontend`: guarda de sessão no `App.tsx` (401 devolve para o login) e identidade no cabeçalho.
- [x] `backend/tests/test_auth.py` cobrindo os 7 acceptance criteria.
- [x] Adaptar a suíte existente para autenticar (fixture de cliente logado), sem afrouxar asserção.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0100-autenticacao-de-sessao/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
