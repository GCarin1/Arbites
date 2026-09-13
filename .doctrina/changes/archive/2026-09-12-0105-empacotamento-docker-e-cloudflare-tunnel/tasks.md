# Tasks — Change 0105-empacotamento-docker-e-cloudflare-tunnel

- [x] `Dockerfile` em dois estágios, rodando como usuário sem privilégio e com healthcheck.
- [x] `docker-compose.yml` com Arbites + cloudflared, sem publicar porta no host.
- [x] `.env.example` com bootstrap do admin, cadastro e token do túnel; `.env` no `.gitignore`.
- [x] `docs/self-hosting.md`: arquitetura, subida, túnel, primeiros passos de admin, backup, operação.
- [x] Registrar no guia por que a aplicação não passa pelo proxy do BFFless.
- [x] Ponteiro no `README.md`.
- [x] Validar estaticamente: compose é YAML válido e sem porta publicada, caminhos do Dockerfile existem, `arbites.api:app` importa, rota de health registrada. O `docker build` em si fica para o servidor — não há Docker nesta máquina.

## Closing steps

- [x] Apply the change (chore: sem deltas de spec).
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0105-empacotamento-docker-e-cloudflare-tunnel/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
