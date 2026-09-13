# Change 0117-avatar-conta-servido-cache-control — avatar da conta e servido sem Cache-Control: o navegador guarda a imagem antiga e um intermediario pode guardar imagem de uma conta

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** profile

## Why

avatar da conta e servido sem Cache-Control: o navegador guarda a imagem antiga e um intermediario pode guardar imagem de uma conta

## What

- `profile` (spec MODIFIED): o avatar passa a declarar cache privado com
  revalidação obrigatória.
- `backend/arbites/api.py`: o cabeçalho na resposta do avatar.
- `backend/tests/test_avatar.py`: o cabeçalho e a troca de foto refletida
  no ETag.

## Scope boundaries

- Não mexe no contador de versão do cliente: ele continua útil para
  atualizar a imagem sem recarregar a página.
- Não toca nas demais rotas que servem arquivo (evidência, artefato), que
  têm outro ciclo de vida e merecem decisão própria.
- Não introduz CDN nem política de cache no túnel; a resposta passa a dizer
  o que ela é, e cada camada respeita.

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
