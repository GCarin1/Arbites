# ADR 0017 — Credencial de CI por variável de ambiente onde não há cofre do SO

- **Status:** accepted
- **Date:** 2026-09-14
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** `backend/tests/test_sem_cofre.py`
- **Landed:** 2026-09-14

## Context

A ADR 0008 decidiu que o PAT do GitHub mora **exclusivamente** no cofre do
sistema operacional, e rejeitou explicitamente "token em arquivo de config
(`arbites.yaml` ou `.env`)" com um motivo que continua correto: o workspace é
versionável e compartilhável, então segredo ali vaza trivialmente.

O que a 0008 não previu é a instância que roda em **container**. O repositório
publica um `Dockerfile` e um `docker-compose.yml`, e numa imagem enxuta não
existe keychain nenhum: a primeira chamada a `keyring` levanta
`NoKeyringError`.

Isso produziu duas consequências, uma delas grave:

1. **A aplicação inteira caía com 500.** A tela Problemas passou a perguntar
   pelo estado da credencial em todo carregamento (change 0157), e a pergunta
   explodia. Uma funcionalidade de CI derrubou a navegação inteira.
2. **A credencial não tinha como ser configurada.** `PUT` no token também
   explodia, então automação e observabilidade ficavam inalcançáveis no
   deployment que o próprio projeto publica.

## Decision

Onde não há cofre do SO, a credencial de CI pode vir da **variável de ambiente
do processo** (`ARBITES_GITHUB_TOKEN`), e o ambiente tem **precedência** sobre
o cofre quando ambos existem.

Três limites que fazem isto não ser a alternativa que a 0008 rejeitou:

- **Ambiente do processo não é arquivo do workspace.** Não viaja com o
  workspace, não entra no git e não é lido por ferramenta nenhuma que abra o
  repositório. É o mesmo canal por onde `ARBITES_ADMIN_PASSWORD` já chega.
- **A regra de nunca devolver o valor continua valendo.** A API expõe status,
  origem (`keyring` | `env`) e se dá para guardar — nunca o token.
- **Ausência de cofre é resposta, não acidente.** Ler devolve "não há
  credencial"; guardar recusa com `409` explicando a saída; e a falta aparece
  como problema na tela, com o remédio, em vez de um campo que recusa em
  silêncio quando alguém tenta usá-lo.

## Alternatives considered

1. **Instalar `keyrings.alt` na imagem** (cofre em arquivo texto) — rejeitado:
   o "cofre" seria um arquivo em claro dentro do container, com a aparência de
   segurança e nenhuma. Um segredo em texto plano é melhor quando se sabe que
   ele está em texto plano.
2. **Montar o keychain do host no container** — rejeitado: acopla a imagem ao
   sistema de quem hospeda e não funciona em host nenhum sem sessão gráfica,
   que é o caso de um servidor doméstico.
3. **Deixar a automação de CI simplesmente indisponível em container** —
   rejeitado: o projeto publica o `docker-compose.yml` como forma de instalar,
   e ADR 0016 (observabilidade) depende dessa credencial. Publicar um caminho
   de instalação onde metade do produto não liga não é uma decisão, é um
   descuido.

## Consequences

**Positive**

- A instância em container funciona, e a de desktop não muda em nada.
- A ausência de cofre é dita em voz alta, com o remédio, em vez de virar um
  500 ou um campo que recusa depois.

**Negative**

- Variável de ambiente é visível em `docker inspect` e no histórico do shell
  de quem subiu o stack — o mesmo custo que o `docker-compose.yml` já
  reconhece para a senha de bootstrap do admin.
- Duas origens possíveis para a credencial exigem que a tela diga qual está
  valendo; sem isso, "troquei o token e não mudou nada" viraria mistério.
