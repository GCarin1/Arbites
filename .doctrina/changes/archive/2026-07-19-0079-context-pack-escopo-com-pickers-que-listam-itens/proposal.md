# Change 0079-context-pack-escopo-com-pickers-que-listam-itens — context-pack: escopo com pickers que listam itens + autocomplete, toggles de secao (CTs/defeitos/decisoes), ultimo resultado por CT, decisoes em qualquer escopo, preview com contagens e copiar/baixar

- **Status:** applied
- **Applied:** 2026-07-19
- **Date:** 2026-07-19
- **Owner:**
- **Affects specs:** context-pack

## Why

O card de Context Pack confunde: os três campos de escopo dizem "(opcional)",
mas o backend exige ao menos um (422 `scope_required`) — então o botão fica
desabilitado com só um tooltip e "não dá para baixar". Além disso o usuário
precisa saber o ID de cor (o campo não LISTA os itens disponíveis), não há
preview do que vai no arquivo, e ADRs só entram quando se filtra por squad.

## What

- **Escopo continua obrigatório** (evita export gigante sem querer), mas os
  três campos passam a **listar os itens reais** e filtrar conforme se
  digita (epic/story via `GET /requirements?kind=`, squad via `GET /squads`,
  com `<datalist>` — lista na abertura, delimita ao digitar). UI corrigida:
  sem "(opcional)" enganoso, hint inline de "escolha ao menos um escopo".
- **Alternadores por seção** (decisão do usuário): checkboxes para incluir/
  excluir **Casos de teste**, **Defeitos** e **Decisões** no pack.
- **Decisões em qualquer escopo** (não só squad): com `include_decisions`
  ligado, o pack inclui as decisões aceitas relevantes — as do squad quando
  há filtro de squad, senão as ADRs aceitas do projeto (contexto
  arquitetural transversal para o agente externo).
- **Último resultado por CT** (opt-in): anexar a cada CT o último status de
  execução (`results`: status + quando) — o agente vê o estado atual, não
  só o roteiro.
- **Preview + contagens**: novo `format=json` em `GET /context-pack`
  devolvendo `{scope, counts, bytes, markdown}`. O card mostra
  "Inclui: X requisitos · Y CTs · Z defeitos · W decisões (~N KB)" + prévia
  do Markdown, com **Copiar** (clipboard) e **Baixar .md** (blob
  client-side, a partir do markdown já buscado — some o `<a download>`
  desabilitado). Segue o design system (skill `design-system-canonico`).

## Scope boundaries

- Não remove a obrigatoriedade de escopo (decisão do usuário: escopo
  obrigatório, sem export do workspace inteiro).
- Não vira seletor em árvore de CTs (decisão do usuário: filtros de campo
  melhorados) — a granularidade é epic/story/squad, não CT a CT.
- Mantém o endpoint `format=md` (attachment) funcionando para link direto;
  a UI passa a usar `format=json` + download client-side.
- Não envia o pack a nenhum provider de IA (continua export puro).

## Verification

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] `format=json` devolve counts/bytes/markdown; toggles removem as seções; decisões entram sem squad; último resultado por CT aparece com opt-in — `backend/tests/test_context_pack.py`.
- [x] `npm run build` limpo; os 3 campos listam itens e filtram ao digitar, e o preview mostra contagens + Copiar/Baixar (revisão visual).

## Open questions

<!-- List unresolved decisions. Empty if none. -->
