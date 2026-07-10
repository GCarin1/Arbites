# Change 0032-repositorios-test-cases-requisitos-execucoes-nom — repositorios (test cases/requisitos/execucoes): nomes aparecem centralizados na linha (botao herda justify-content:center do estilo base) — alinhar a esquerda; e nova visualizacao com box-drawing tree connectors (branches ├── └── e linhas │) para hierarquia intuitiva

- **Status:** applied
- **Applied:** 2026-07-10
- **Date:** 2026-07-10
- **Owner:**
- **Affects specs:** (none — chore)

## Why

repositorios (test cases/requisitos/execucoes): nomes aparecem centralizados na linha (botao herda justify-content:center do estilo base) — alinhar a esquerda; e nova visualizacao com box-drawing tree connectors (branches ├── └── e linhas │) para hierarquia intuitiva

## What

- **styles.css** — `.repo-file-main` ganha `justify-content: flex-start` (não
  herdar `center` do estilo base de `button` — era o que centralizava id+título).
  Novo `.tree-prefix` (monospace) para os conectores; `.repo-row` mais compacto.
- **TcRepository/ReqRepository/ExecutionsRepo** — árvore com **box-drawing**:
  cada linha recebe `├── `/`└── ` conforme seja o último irmão e o prefixo dos
  ancestrais (`│   `/`    `), substituindo o `paddingLeft` por posição estrutural.
  Isso torna a hierarquia explícita e alinha os itens exatamente sob sua pasta.

## Bugs corrigidos (skills)

- Nomes centralizados na linha (button herda `justify-content:center`) → skill
  `botao-como-item-de-lista-heranca-justify`.

## Scope boundaries

- UI-only; sem backend/spec. Execuções usam o ano de criação como "pasta".

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Build do frontend verde.
- [x] Chore UI; skill do bug criada.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
