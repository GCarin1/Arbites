# Change 0112-versionamento-dos-casos-de-teste-com-git-no — Versionamento dos casos de teste com git no workspace

- **Status:** applied
- **Applied:** 2026-09-13
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** testcases

## Why

Transformar o workspace num repositorio git de verdade: init automatico e commit por acao semantica da interface, assinado com o autor da sessao, em vez de um commit por gravacao. Historico, comparacao entre versoes e restauracao expostos numa aba do proprio caso de teste. Edicao feita por fora, no Obsidian, tambem vira commit, com autoria externa.

## What

- `testcases` (spec MODIFIED): o workspace vira repositório git, com commit
  por ação semântica e histórico exposto no próprio caso.
- `backend/arbites/versioning.py` (novo): `git init`, commit por ação,
  histórico, comparação e restauração — tudo por subprocess, com timeout.
- `backend/arbites/api.py`: as quatro rotas de versão e o commit acoplado
  às ações de criar, editar, mover e excluir.
- `backend/tests/test_versioning.py`: a prova dos três critérios.
- `frontend/src/components/TestCaseEditor.tsx`: a aba de histórico, com
  comparação e restauração.

## Scope boundaries

- Não versiona executions, defeitos nem os demais artefatos: o escopo desta
  mudança é o caso de teste, que é onde a pergunta "o que mudou aqui?"
  aparece todo dia.
- Não conversa com remoto: sem push, sem pull, sem credencial. O
  repositório é local, como todo o resto do produto.
- Não substitui a lixeira: excluir continua movendo para `trash/`, e o
  commit apenas registra que saiu.
- Não toca no mapa de risco, que já lê `git log` de OUTROS repositórios
  (os do código sob teste) e continua read-only lá.

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
