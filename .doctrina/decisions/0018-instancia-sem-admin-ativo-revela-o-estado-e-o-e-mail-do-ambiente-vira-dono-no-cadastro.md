# ADR 0018 — Instancia sem admin ativo revela o estado e o e-mail do ambiente vira dono no cadastro

- **Status:** accepted
- **Date:** 2026-09-14
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** `backend/arbites/auth.py`, `backend/arbites/api.py`, `backend/tests/test_primeiro_dono.py`, `frontend/src/components/Login.tsx`
- **Landed:** 2026-09-14 — `backend/arbites/auth.py`, `backend/arbites/api.py`, `backend/tests/test_primeiro_dono.py`

<!--
Evidence anchors the decision to reality. Once accepted, cite the file(s)
that prove this decision is actually implemented, in backticks, e.g.
"- **Evidence:** `proto/order.proto`, `services/gateway/grpc.ts`".
`doctrina validate` warns when cited evidence is missing on disk (the
decision drifted from the code) or when an accepted ADR cites none. For a
process decision with no code artifact, write "n/a — <why>".

Landed is the non-mutating "this decision is now implemented and verified
here" stamp. Many ADRs are accepted at design time with "Evidence: n/a — no
implementation yet"; once the capability ships, run
"doctrina decision land NNNN `path/to/proof.ts` ..." to record the date and
proof without editing the immutable body. A filled Landed satisfies the
accepted-ADR evidence check.
-->

## Context

Toda conta criada pelo formulário público (`POST /auth/register`) nasce
`viewer`/`pending`: alguém com papel admin precisa liberar antes do primeiro
login. A regra é boa enquanto existe um admin — e ela existe porque o
`bootstrap_admin` cria um a partir de `ARBITES_ADMIN_EMAIL` e
`ARBITES_ADMIN_PASSWORD` no start.

Quando essas variáveis não chegam ao processo — o caso real que motivou esta
decisão: instalação sem Docker, `.env` não lido antes da change 0165 — a
instância sobe com ZERO admins ativos. A partir daí o cadastro pelo
formulário é um beco sem saída: a conta fica pendente e não existe ninguém
no sistema com poder de aprová-la. Pior, nada na tela diz isso, e o login
responde o mesmo 401 opaco de senha errada (deliberado, ADR 0011 e o
não-enumerar contas), então a pessoa fica tentando a senha.

A change 0166 deu a saída pela linha de comando (`python -m arbites admin`),
mas ela só serve a quem descobre que ela existe.

## Decision

Numa instância **sem nenhum admin ativo**, o Arbites passa a fazer duas
coisas:

1. **Revela o estado.** `GET /auth/me` responde `no_admin: true` e
   `owner_declared: true|false` para quem ainda não entrou, e a tela de
   login exibe o aviso correspondente — cadastrar-se com o e-mail do
   ambiente, ou rodar o comando local.
2. **Deixa o e-mail do ambiente tomar posse.** Um cadastro cujo e-mail é
   exatamente `ARBITES_ADMIN_EMAIL` (comparação sem caixa) nasce
   `admin`/`active` em vez de `viewer`/`pending`, com a senha escolhida por
   quem se cadastrou.

As duas condições valem juntas e só enquanto `count_active_admins() == 0`.
Assim que existe um admin ativo, o cadastro volta a ser `viewer`/`pending`
para todo mundo, inclusive para o e-mail do ambiente: a posse acontece uma
vez, não é uma porta permanente.

`bootstrap_admin` continua como está e continua não sobrescrevendo a senha
de uma conta que já existe — quem faz isso é o comando local.

## Alternatives considered

1. **Primeiro cadastro vira admin, qualquer e-mail** (o padrão de Jenkins e
   afins). Frictionless, mas é uma tomada de posse por quem chegar primeiro:
   numa máquina de rede com a porta aberta, quem varrer a faixa leva a
   instância. Amarrar ao `ARBITES_ADMIN_EMAIL` custa uma variável e move a
   decisão para quem controla o processo — a mesma mão do ADR 0017.
2. **Só avisar, sem deixar ninguém tomar posse.** Tira o beco sem saída mas
   mantém a fricção: o operador tem de ir ao terminal mesmo tendo declarado
   o e-mail. Fica como o caminho para quem não declarou nada.
3. **Não revelar `no_admin`.** Mantém a instância opaca de fora, coerente
   com o 401 indistinguível. Rejeitado: o que o 401 protege é *quais contas
   existem*, e `no_admin` não responde isso. O silêncio aqui não protegia
   nada e custava a saída.

## Consequences

**Positive**

- O beco sem saída deixa de existir: quem se cadastra numa instância órfã é
  avisado antes, e o operador que declarou o e-mail entra sem ir ao terminal.
- A senha do dono é escolhida por ele, não vem de variável de ambiente
  visível em `docker inspect` e no histórico de shell.

**Negative**

- `GET /auth/me` passa a revelar, sem sessão, que a instância não tem admin
  ativo — um sinal de que ela está recém-subida ou desgovernada. Aceito: não
  revela nenhum e-mail nem a existência de conta alguma.
- Quem souber o valor de `ARBITES_ADMIN_EMAIL` e alcançar a instância na
  janela em que ela não tem admin cria o admin. A janela fecha no primeiro
  admin ativo; quem controla o ambiente escolhe o e-mail.

**Neutral**

- A resposta de `POST /auth/register` ganhou o campo `admin`, que a tela usa
  para dizer qual das duas coisas aconteceu.
