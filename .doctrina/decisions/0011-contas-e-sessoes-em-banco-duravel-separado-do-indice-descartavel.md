# ADR 0011 — Contas e sessoes em banco duravel separado do indice descartavel

- **Status:** accepted
- **Date:** 2026-09-12
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decidido ao abrir o change 0100; landa com a implementação
- **Landed:** 2026-09-12 — `backend/arbites/auth.py`, `backend/tests/test_auth.py`

## Context

Até aqui o Arbites tinha dois lugares para guardar estado e uma regra clara
para cada: o filesystem do workspace é a fonte de verdade (ADR 0001) e
`.arbites/index.db` é índice descartável, apagável e reconstruível a
qualquer momento. Segredos não entram em nenhum dos dois — vão para o
keyring do SO (ADR 0008).

Autenticação não cabe em nenhuma das três gavetas:

- **No workspace** não pode. O workspace é Markdown legível, editável no
  Obsidian e versionado em git para colaboração — é exatamente o lugar onde
  um hash de senha não pode estar.
- **No índice descartável** não pode. `reindex_full` roda a cada boot e a
  premissa do SC1 é que apagar `index.db` não perde nada. Conta e sessão
  são justamente o que não pode ser reconstruído a partir do disco.
- **No keyring** não cabe. O keyring guarda um segredo do operador, não uma
  tabela relacional de N usuários com papel, status e histórico de
  tentativa. E o M14 põe a aplicação num container Linux headless, onde não
  há cofre de SO para conversar.

## Decision

Contas, sessões e tentativas de login vivem num terceiro store: um SQLite
**durável** em `.arbites/auth.db`, com conexão própria, separado do índice.
Nenhum caminho de indexação, watcher ou reconstrução o lê ou escreve; ele
não é fonte de verdade de nada que a UI mostre como artefato.

Escopo da decisão: identidade e sessão. Segredos de integração (PAT do
GitHub, chaves de IA) continuam sob a ADR 0008; este ADR não os move.

Consequência operacional que fica registrada: `.arbites/` inteiro é
gitignorável (workspace-core, Optional), então `auth.db` está fora do git
por construção — e, por isso mesmo, precisa entrar explicitamente na
rotina de backup do servidor, junto do volume do workspace.

## Alternatives considered

1. **Tabelas de usuário dentro do `index.db`** — rejeitado: o primeiro
   `reindex` que caísse num banco corrompido, ou o primeiro `rm index.db`
   sugerido pela própria documentação, apagaria todas as contas. Misturar
   dado reconstruível com dado insubstituível no mesmo arquivo quebra a
   garantia que o SC1 vende.
2. **Usuários como Markdown no workspace** (`users/U-0001.md`) — rejeitado:
   coerente com "tudo que existe na UI existe no disco", mas põe hash de
   senha num arquivo versionado e sincronizado. O ganho de coerência não
   paga o risco.
3. **Postgres** — rejeitado: contraria o local-first e obriga um segundo
   container para uma tabela de usuários que, no uso previsto, tem dezenas
   de linhas.
4. **Delegar a identidade ao BFFless / SuperTokens que já roda no servidor**
   — rejeitado por três motivos concretos: o proxy dele remove os headers
   `cookie` e `authorization` e não documenta injeção de identidade, então
   o Arbites nunca saberia quem é o usuário (matando a autoria do 0104);
   não há log de auditoria documentado, que teria de ser construído aqui de
   qualquer forma; e o teto de 60s do proxy quebraria o SSE do runner
   (`GET /runs/{exec_id}/stream`). Fica registrado para não se rediscutir.

## Consequences

**Positive**

- Apagar `index.db` continua sendo uma operação segura e documentável.
- Nenhum dado de conta entra em git, mesmo com o workspace versionado.
- Sem dependência de cofre de SO, a aplicação roda em container headless.
- Um único arquivo concentra o que precisa de backup e de cuidado.

**Negative**

- Passa a haver estado insubstituível fora do workspace: quem só fizer
  backup do workspace perde as contas. Precisa estar documentado no M14.
- Duas conexões SQLite no processo, com dois ciclos de vida distintos.
- Contas deixam de ser inspecionáveis no Obsidian, ao contrário de todo o
  resto do produto.

**Neutral**

- Nada impede migrar depois para Postgres ou para um IdP externo: o acesso
  fica atrás de um módulo (`backend/arbites/auth.py`), não espalhado.
