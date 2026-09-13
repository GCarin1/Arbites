# Change 0119-e-mails-diferentes-colidem-mesmo — e-mails diferentes colidem no mesmo slug e duas contas passam a compartilhar perfil memoria de IA e avatar

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** profile

## Why

e-mails diferentes colidem no mesmo slug e duas contas passam a compartilhar perfil memoria de IA e avatar

## What

- `profile` (spec MODIFIED): a identidade de arquivo por conta passa a ser
  unívoca, e o nome antigo é adotado em vez de abandonado.
- `backend/arbites/api.py`: um helper `_account_slug()` usado pelo perfil e
  pelo avatar, e a adoção do caminho antigo na primeira leitura.
- `backend/tests/test_profile_identity.py`: a prova dos dois critérios.

## Scope boundaries

- Não muda o `slugify()` do workspace, que continua certo para o que ele
  faz: nomear artefatos a partir de títulos, onde colidir é aceitável
  porque o ID no frontmatter é que identifica (ADR 0002).
- Não troca o nome do arquivo por um id numérico: um workspace aberto no
  Obsidian precisa dizer de quem é cada arquivo, e `7.md` não diz.
- Não mexe em autenticação nem em papéis; o e-mail continua sendo a
  identidade da conta.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).

## Open questions

Nenhuma.
