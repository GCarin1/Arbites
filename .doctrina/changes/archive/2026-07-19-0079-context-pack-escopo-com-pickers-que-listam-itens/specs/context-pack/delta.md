# Delta — context-pack (change 0079)

**Operation:** MODIFIED

Escopo com pickers que listam itens, toggles de seção, decisões em qualquer
escopo, último resultado por CT, e preview com contagens. O conteúdo já foi
mesclado direto em `.doctrina/specs/context-pack/spec.md` (deltas prose,
merge manual).

## MODIFIED — Requirements (EARS)

### Ubiquitous (adicionar / ajustar)

- The system shall aceitar em `GET /context-pack` os toggles opcionais
  `testcases`, `defects`, `decisions` (default `true`) e `last_result`
  (default `false`), incluindo/excluindo cada seção do bundle. [unverified]
- The system shall expor `GET /context-pack?format=json` devolvendo
  `{scope, counts, bytes, markdown}` — `counts` com requisitos/CTs/defeitos/
  decisões incluídos — para preview na UI; sem `format=json` mantém o
  Markdown como `attachment`. [unverified]
- The system shall, quando `last_result` está ligado, anexar a cada caso de
  teste o último resultado de execução registrado (status + data, da tabela
  `results`). [unverified]

### Ubiquitous (substituir "incluir decisões do squad filtrado")

- The system shall incluir as decisões arquiteturais aceitas relevantes ao
  escopo quando `decisions` está ligado: as do squad quando `squad` é
  informado, senão as ADRs aceitas do projeto (contexto arquitetural
  transversal) — não mais restrito ao filtro de squad. [unverified]

### State-driven (adicionar)

- While o card de Context Pack está aberto, the system shall listar os itens
  reais de escopo (epics/stories via `GET /requirements?kind=`, squads via
  `GET /squads`) e filtrá-los conforme o usuário digita, mantendo o escopo
  obrigatório com hint inline (sem rótulo "(opcional)" enganoso), e mostrar
  preview com contagens (`format=json`) e ações Copiar/Baixar (download
  client-side a partir do markdown buscado). [unverified]

## Acceptance criteria (append)

6. [unverified] `GET /context-pack?format=json` devolve `counts`/`bytes`/
   `markdown`; os toggles `testcases`/`defects`/`decisions` removem as
   respectivas seções; `last_result` anexa o último status por CT — verified
   by `backend/tests/test_context_pack.py`.
7. [unverified] Com `decisions` ligado e sem `squad`, o bundle inclui as
   decisões aceitas do projeto; com `squad`, as daquele squad — verified by
   `backend/tests/test_context_pack.py`.
8. [unverified] O card lista epics/stories/squads e filtra ao digitar, e o
   preview mostra contagens + Copiar/Baixar — verified by build + revisão
   visual (`frontend/src/components/AiAssist.tsx`).
