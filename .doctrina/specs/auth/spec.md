# Spec Delta — capability: auth

**Operation:** ADDED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

# Spec — auth

**Capability:** auth
**Status:** active
**Implementation:** verified — `backend/arbites/auth.py`, `backend/arbites/api.py` (rotas /auth/* + gate), `frontend/src/components/AuthGate.tsx`
**Realizes:** SC15
**Last updated:** 2026-09-12
**Version:** 0.2.0

## Purpose

Transforma o Arbites de processo local sem porteiro numa instância que pode
ficar acessível fora da máquina do QA. Cobre a identidade: contas, senha,
sessão, cadastro com aprovação e o gate que recusa qualquer rota da API sem
sessão válida. Não cobre o que se faz com a identidade depois de
autenticada — papel por rota (`workspace-core`), painel de gestão (`admin`),
log de escrita (`audit`) e autoria de artefato (`profile`) são outras
capabilities.

A decisão estrutural é que conta não é artefato de workspace: hash de senha
e sessão nunca entram em Markdown versionável nem no índice descartável.
Eles vivem num banco durável próprio, `.arbites/auth.db` (ADR 0011).

## Requirements (EARS)

### Ubiquitous

- The system shall persistir contas, sessões e tentativas de login em
  `.arbites/auth.db` — banco SQLite **durável**, distinto do índice
  descartável `.arbites/index.db`; reindex e reconstrução do índice nunca
  o leem nem o escrevem.
- The system shall armazenar a senha apenas como hash Argon2id com salt
  por usuário, nunca em texto puro e nunca de forma reversível.
- The system shall dar a cada conta um e-mail único (comparado
  case-insensitive), um papel entre `admin`, `editor` e `viewer`, e um
  status entre `pending`, `active`, `disabled` e `rejected`.
- The system shall expor `POST /auth/register`, `POST /auth/login`,
  `POST /auth/logout`, `GET /auth/me` e `POST /auth/password`.
- The system shall emitir a sessão como cookie `arbites_session` httpOnly,
  `SameSite=Lax`, `Path=/`, marcado `Secure` quando a requisição chega por
  HTTPS, contendo apenas um identificador opaco de 256 bits de entropia —
  nunca dados do usuário.
- The system shall guardar no banco somente o hash SHA-256 do
  identificador de sessão, de modo que um vazamento do banco não permita
  reutilizar sessões vivas.
- The system shall expirar a sessão por inatividade (default 12 horas) e
  por idade absoluta (default 7 dias).
- The system shall exigir sessão válida em toda rota sob o prefixo da API,
  exceto `POST /auth/register`, `POST /auth/login`, `GET /auth/me`,
  `GET /health` e os estáticos do SPA.
- The system shall derivar o IP do cliente de `CF-Connecting-IP` quando
  presente, caindo para o primeiro salto de `X-Forwarded-For` e depois
  para o endereço do socket — a instância roda atrás de túnel/proxy.
- The system shall registrar toda tentativa de autenticação (sucesso e
  falha) com e-mail informado, resultado, IP e user-agent.
- The system shall atribuir a cada papel um alcance fixo — `viewer` só lê, `editor` lê e escreve os artefatos de QA (requisitos, casos de teste, execuções, defeitos, afazeres, reuniões, decisões, daily) e dispara execuções de alvos já configurados, e `admin` acumula tudo isso mais as superfícies governadas.
- The system shall exigir papel `admin` nas superfícies governadas: `PUT /targets` (define o executável e o diretório do subprocess), `GET /automation/browse-features` (navega o filesystem do servidor), `GET|PUT /targets/{name}/env` e `GET /env/catalog` (segredos do projeto-alvo), `PUT /settings/github/token` e as chaves de IA, e `POST /import/xray` e `POST /import/xray/confirm`.
- The system shall manter um registro de interruptores administráveis — `local_runner`, `filesystem_browse`, `target_env`, `ai` e `xray_import` — persistido no mesmo banco durável das contas, cada um ligado por padrão para não alterar em silêncio o comportamento da instalação local.
- The system shall expor `GET /admin/switches` (estado de todos, legível por qualquer sessão para que a UI esconda o que está desligado) e `PUT /admin/switches/{name}` (apenas `admin`), registrando quem alterou e quando.

### Event-driven

- When um cadastro é submetido, the system shall criar a conta com status
  `pending` e papel `viewer`, sem abrir sessão — conta pendente não
  autentica.
- When um admin aprova uma conta pendente, the system shall marcá-la
  `active`; ao recusar, `rejected`.
- When o processo sobe e não existe nenhuma conta com papel `admin`, the
  system shall criar a conta de bootstrap a partir de `ARBITES_ADMIN_EMAIL`
  e `ARBITES_ADMIN_PASSWORD`, já `active`, com `must_change_password`.
- When a senha de uma conta muda, the system shall invalidar todas as
  sessões dela e emitir uma sessão nova para o cliente que originou a troca
  — sessão roubada cai, quem acertou a senha continua dentro.
- When uma conta é desativada, recusada ou tem o papel alterado, the system
  shall invalidar todas as sessões dela imediatamente.
- When uma requisição chega com cookie de sessão expirado ou desconhecido,
  the system shall responder 401 com código `unauthenticated` e apagar o
  cookie.
- When uma requisição de escrita (qualquer método que não seja GET, HEAD ou OPTIONS) chega de uma sessão com papel `viewer`, the system shall recusá-la com 403 e código `forbidden`, exceto a troca da própria senha e o logout.
- When uma rota governada por um interruptor desligado é chamada, the system shall recusá-la com 403 e código `feature_disabled`, nomeando o interruptor responsável.

### State-driven

- While uma conta acumulou 5 falhas de login nos últimos 15 minutos, the
  system shall recusar novas tentativas dela por 15 minutos com HTTP 429 e
  código `locked_out`, contando as tentativas por conta e por IP.
- While a conta está `pending`, `disabled` ou `rejected`, the system shall
  recusar o login com exatamente a mesma resposta de credencial inválida.
- While a conta tem `must_change_password`, the system shall permitir a
  sessão mas recusar toda rota que não seja `POST /auth/password`,
  `GET /auth/me` ou `POST /auth/logout`, com código `password_change_required`.
- While `ARBITES_SIGNUP` vale `off`, the system shall recusar
  `POST /auth/register` com 403 e código `signup_disabled`.
- While o papel da sessão não alcança a rota, the system shall responder 403 com código `forbidden` — nunca 404, para não transformar autorização em adivinhação de rota.

### Unwanted-behavior (must-not)

- The system shall not aceitar a sessão por querystring, por header
  `Authorization` ou por qualquer canal legível a JavaScript; somente o
  cookie httpOnly.
- The system shall not gravar hash de senha, identificador de sessão ou
  e-mail de conta em arquivo do workspace — nada de conta entra em git.
- The system shall not revelar, em erro de login, se o e-mail existe, se a
  conta está pendente ou se a senha está errada; a resposta é sempre a
  mesma.
- The system shall not permitir que o último admin `active` seja
  desativado, recusado ou rebaixado de papel.
- The system shall not aceitar senha com menos de 12 caracteres.
- The system shall not apagar registro de tentativa de login; o contador do
  lockout zera no último sucesso, nunca removendo linhas — "cinco falhas e
  então um acerto" é justamente a evidência que não pode sumir quando o
  atacante finalmente entra.
- The system shall not permitir que `PUT /targets` seja alcançado por papel diferente de `admin`; um alvo define o binário e o diretório de trabalho de um subprocess, então configurá-lo equivale a executar código no servidor.
- The system shall not deixar um interruptor desligado ser contornado por outra rota que faça a mesma coisa; o interruptor governa a capacidade, não a URL.

### Optional

- Where a instância roda em rede confiável e o operador aceita o risco, the
  system may aceitar `ARBITES_AUTH=off`, que desliga o gate por completo e
  registra um aviso alto no log de inicialização.

## Acceptance criteria

1. [verified] Um cadastro novo nasce `pending` e o login dele é recusado
   até um admin aprovar — verified by `backend/tests/test_auth.py`.
2. [verified] Login correto devolve `Set-Cookie` httpOnly + SameSite=Lax
   sem dados do usuário no valor, e `GET /auth/me` passa a responder o
   perfil — verified by `backend/tests/test_auth.py`.
3. [verified] Sem cookie, toda rota da API responde 401 `unauthenticated`
   enquanto a rota de login e os estáticos do SPA continuam acessíveis —
   verified by `backend/tests/test_auth.py`.
4. [verified] Cinco falhas seguidas travam a conta por 15 minutos com 429
   `locked_out`, a resposta de e-mail inexistente é byte a byte igual à de
   senha errada, e o sucesso posterior zera o contador sem apagar as falhas
   do registro — verified by `backend/tests/test_auth.py`.
5. [verified] Desativar a conta, ou trocar-lhe o papel, derruba as
   sessões abertas dela na requisição seguinte; trocar a senha derruba as
   outras sessões mas rotaciona a de quem trocou — verified by
   `backend/tests/test_auth.py`.
6. [verified] Subir sem nenhum admin cria a conta de bootstrap a partir
   do ambiente, com troca de senha obrigatória que bloqueia as demais
   rotas até ser feita — verified by `backend/tests/test_auth.py`.
7. [verified] Apagar `index.db` e reindexar não afeta contas nem sessões;
   `auth.db` sobrevive intacto — verified by `backend/tests/test_auth.py`.
8. [verified] Um `viewer` lê tudo por GET e recebe 403 `forbidden` em qualquer escrita, inclusive nas rotas que não existiam quando o papel foi criado — verified by `backend/tests/test_authorization.py`.
9. [verified] Um `editor` cria artefatos e dispara um run local, mas recebe 403 em `PUT /targets`, no navegador de filesystem, no `.env` do alvo, no token do GitHub e no import Xray — verified by `backend/tests/test_authorization.py`.
10. [verified] Desligar `local_runner` faz `POST /runs/local` responder 403 `feature_disabled` citando o interruptor, e religá-lo devolve a rota, sem reiniciar o processo — verified by `backend/tests/test_authorization.py`.
11. [verified] Os interruptores nascem todos ligados, sobrevivem ao reinício do processo e só o `admin` os altera — verified by `backend/tests/test_authorization.py`.

## Maturity

**MVP (committed):**

- Contas locais com e-mail e senha, papel, aprovação de cadastro, sessão
  por cookie, lockout, bootstrap por ambiente.

**Future (aspirational, not committed):**

- Segundo fator (TOTP) obrigatório para `admin`.
- Convite por link com expiração, em vez de cadastro aberto.
- Federação SSO/OIDC contra um provedor externo.

## Out of scope for this spec

- Autorização por papel em cada rota e os kill switches das rotas
  perigosas (ver `workspace-core`).
- Telas e API de gestão de usuários e de acessos (ver `admin`).
- Log de escrita de artefatos (ver `audit`).
- Autoria de artefato a partir da sessão (ver `profile`).
