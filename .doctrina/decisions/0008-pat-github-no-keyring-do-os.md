# ADR 0008 — PAT GitHub no keyring do OS

- **Status:** accepted
- **Date:** 2026-07-03
- **Deciders:** Gcarini
- **Supersedes:** —
- **Superseded by:** —
- **Evidence:** n/a — decisão de segurança do intake; nenhuma implementação ainda (landará com o M4)
- **Landed:** —

## Context

O M4 exige um PAT do GitHub para workflow_dispatch e download de artifacts.
O workspace é versionável em git e legível por qualquer ferramenta —
qualquer segredo em arquivo de config vazaria trivialmente.

## Decision

O PAT (fine-grained, escopo mínimo `actions:read+write` no repo do target)
é armazenado exclusivamente via biblioteca `keyring` no cofre do SO. Nunca
em YAML, nunca no índice, nunca logado. A API expõe apenas o status do
token (`GET /settings/github/token` não retorna o valor). O mesmo padrão
vale para chaves de providers de IA (M5).

## Alternatives considered

1. Token em arquivo de config (`arbites.yaml` ou `.env`) — rejeitado:
   segredo em texto plano num workspace versionável.

## Consequences

**Positive**

- Segredos protegidos pelo cofre nativo do SO; workspace 100% compartilhável.

**Negative**

- Dependência do keychain da plataforma; setup por máquina (não viaja com
  o workspace).

**Neutral**

- `keyring` abstrai Windows Credential Manager / macOS Keychain / Secret
  Service.
