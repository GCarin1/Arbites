# Change 0105-empacotamento-docker-e-cloudflare-tunnel — Empacotamento Docker e Cloudflare Tunnel

- **Status:** applied
- **Applied:** 2026-09-12
- **Date:** 2026-09-12
- **Owner:**
- **Lane:** product (confident; signals: build, documentar) — opened as chore
- **Affects specs:** (none — chore)

## Why

Empacotar o Arbites como imagem Docker (build do frontend, FastAPI servindo o dist, workspace e banco em volume) mais um docker-compose pronto para UmbrelOS, e documentar a exposicao por hostname proprio no Cloudflare Tunnel apontando para a porta interna do container. Inclui as variaveis de ambiente de bootstrap do admin e do segredo de sessao, e a nota de por que a aplicacao nao passa pelo proxy do BFFless.

## What

- `Dockerfile` — build da SPA num estágio, runtime do FastAPI servindo API e
  dist na mesma origem, usuário sem privilégio, healthcheck.
- `docker-compose.yml` — Arbites + `cloudflared`, sem publicar porta no host.
- `.env.example` e `.env` no `.gitignore`.
- `docs/self-hosting.md` — arquitetura, subida, primeiros passos de admin,
  backup, operação, e o registro de por que a aplicação não passa pelo proxy
  do BFFless.
- `README.md` — ponteiro para o guia.

## Scope boundaries

- Não é um app de loja do UmbrelOS (manifesto, ícone, submissão); é um
  compose que roda no Docker do UmbrelOS como em qualquer host.
- Não automatiza a criação do túnel na Cloudflare: o token é gerado no
  painel deles e colado no `.env`.
- Não cobre TLS próprio nem proxy reverso alternativo — o `cloudflared`
  termina o TLS na borda.
- Não muda código da aplicação: tudo o que a exposição exige já entrou nos
  changes 0100 a 0104.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] **NÃO VERIFICADO** — `docker build .` conclui e a imagem sobe
      respondendo `GET /api/v1/health`. Não há Docker na máquina onde este
      change foi escrito; precisa ser rodado no servidor antes de confiar na
      imagem. O que foi verificado no lugar: o `docker-compose.yml` é YAML
      válido e não publica porta no host, todos os caminhos que o
      `Dockerfile` copia existem, `arbites.api:app` é importável e a rota
      `/api/v1/health` do healthcheck está registrada.
- [x] O compose não publica `8347` no host — a única entrada é o túnel.
- [x] O guia cobre backup do `auth.db` explicitamente — é o único dado da
      instalação que não se reconstrói.
- [x] `doctrina verify` continua verde (o change não toca código).

## Open questions

Nenhuma.
