# Spec — businessmap

**Capability:** businessmap
**Status:** active
**Implementation:** planned — M6, gated na migração corporativa. Especificado (intenção fixada); a implementação começa quando o Businessmap substituir o Jira/Xray na B3 e houver acesso à API real (ADR 0007)
**Realizes:** SC10
**Last updated:** 2026-07-06
**Version:** 0.1.0

## Purpose

O fluxo corporativo troca Jira/Xray por **Businessmap** (ex-Kanbanize), que
não cobre gestão de testes — este é o motivo de existir do Arbites. O
Businessmap passa a hospedar os work items (cards ≈ epics/stories). Esta
capability integra o Arbites ao Businessmap **como o Xray já é integrado**:
vínculo por chave externa e import pontual de cards → requisitos-espelho.
Segue ADR 0007 (integração externa é ponteiro + migração pontual, não
sincronização contínua) e o princípio single-user local (nada sai da
máquina sem ação explícita).

Esta spec **fixa a intenção** de M6; o contrato concreto da API do
Businessmap (endpoints, auth, IDs de board/card) é preenchido quando a
migração concretizar — mesma postura da ci-automation ("validação contra a
API real pendente do primeiro uso").

## Requirements (EARS)

### Ubiquitous

- The system shall permitir vincular um requisito (epic/story) ou defeito a
  um card do Businessmap pela `external_key` já existente (ponteiro, não
  cópia — igual ao vínculo Jira/Xray de hoje).
- The system shall guardar o token de acesso ao Businessmap no keyring do
  SO (ADR 0008), nunca em YAML.

### Event-driven

- When o usuário solicita importar um board/card do Businessmap, the system
  shall apresentar um preview (nada gravado) e, na confirmação, criar
  requisitos-espelho locais idempotentes por `external_key` (reimportar o
  mesmo card é seguro — pulado se já migrado), espelhando o `import/xray`
  (preview → confirm).

### State-driven

- While nenhum token do Businessmap está configurado, the system shall
  ocultar/desabilitar as funções de Businessmap mantendo todo o resto da
  plataforma funcional.

### Unwanted-behavior (must-not)

- The system shall not sincronizar automaticamente nem escrever no
  Businessmap sem ação explícita do usuário (a plataforma é local-first; o
  Businessmap é a fonte corporativa, lida sob demanda).
- The system shall not tornar qualquer função central dependente do
  Businessmap (100% funcional offline/sem integração).

### Optional

- Where a API do Businessmap expõe o status dos cards, the system may exibir
  esse status ao lado do requisito-espelho (read-only).

## Acceptance criteria

1. [unverified] Vincular um requisito/defeito a um card do Businessmap por
   `external_key` e navegar até o card — verified by `tests/test_businessmap.py`.
2. [unverified] Import pontual de cards do Businessmap gera requisitos-espelho
   idempotentes (reimport pula os já migrados), com preview antes de gravar —
   verified by `tests/test_businessmap.py`.
3. [unverified] Sem token configurado, a plataforma opera integralmente —
   verified by `tests/test_businessmap.py`.

## Maturity

**MVP (committed quando M6 destravar):**

- Vínculo por `external_key`, token no keyring, import pontual cards →
  requisitos-espelho com preview idempotente.

**Future (aspirational, not committed):**

- Push de cobertura/pass rate para cards do Businessmap; status de card ao
  vivo no dashboard.

## Out of scope for this spec

- Sincronização bidirecional contínua (ADR 0007: integração é pontual).
- Substituir o Businessmap como ferramenta de work items (o Arbites cobre
  testes, não gestão de produto).
- Implementação antes da migração corporativa concretizar (gated).
