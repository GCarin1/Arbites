# Spec — context-pack

**Capability:** context-pack
**Status:** active
**Implementation:** verified
**Realizes:** n/a — capability nova (Context Pack para agentes de IA), fora do escopo do intake original; surgiu de uma sessão de brainstorm sobre memória/contexto para IA
**Last updated:** 2026-07-19
**Version:** 0.2.0

## Purpose

Empacota o contexto de um escopo do projeto (epic, story ou squad) — os
requisitos, casos de teste, defeitos (com causa raiz e correção, quando
registrados) e decisões arquiteturais relacionados — num único documento
Markdown, pronto para ser colado ou anexado a um agente de IA externo
(Cursor, Claude Code, OpenAI Codex, Roo Code, Aider, etc.) que precisa de
contexto do projeto sob teste sem ter acesso direto ao workspace do Arbites.
É um export puro: não chama nenhum provider de IA e não depende de um
provider configurado.

## Requirements (EARS)

### Ubiquitous

- The system shall expor `GET /context-pack` que devolve um único documento
  Markdown (`text/markdown`, com `Content-Disposition: attachment`)
  contendo os requisitos (epic/stories), casos de teste e defeitos do
  escopo pedido, cada um com seu corpo completo lido do disco (não apenas
  metadados).
- The system shall aceitar os filtros `epic`, `story` e `squad` (todos
  opcionais individualmente, mas ao menos um é obrigatório) para delimitar
  o escopo do bundle.
- The system shall incluir, para cada defeito no escopo, a causa raiz e a
  correção quando registradas (ver capability `defects`, Lições
  Aprendidas), permitindo que o agente de IA externo aprenda com incidentes
  passados do mesmo escopo.
- The system shall incluir as decisões arquiteturais aceitas relevantes ao
  escopo quando `decisions` está ligado: as do squad quando `squad` é
  informado, senão as ADRs aceitas do projeto (contexto arquitetural
  transversal para o agente externo) — não mais restrito ao filtro de squad.
- The system shall aceitar os toggles opcionais `testcases`, `defects`,
  `decisions` (default `true`) e `last_result` (default `false`),
  incluindo/excluindo cada seção do bundle.
- The system shall, quando `last_result` está ligado, anexar a cada caso de
  teste o último resultado de execução registrado (status + data, da tabela
  `results`).
- The system shall expor `GET /context-pack?format=json` devolvendo
  `{scope, counts, bytes, markdown}` (com `counts` de requisitos/CTs/
  defeitos/decisões incluídos) para preview na UI; sem `format=json` mantém
  o Markdown como `attachment`.

### Event-driven

- When `story` é informado, the system shall restringir o bundle a essa
  story específica (mesmo que pertença a um epic com outras stories).
- When `epic` é informado sem `story`, the system shall incluir todas as
  stories daquele epic.

### State-driven

- While o card de Context Pack está aberto, the system shall listar os itens
  reais de escopo (epics/stories via `GET /requirements?kind=`, squads via
  `GET /squads`) e filtrá-los conforme o usuário digita, mantendo o escopo
  obrigatório com hint inline (sem rótulo "(opcional)" enganoso), e mostrar
  preview com contagens (`format=json`) e ações Copiar/Baixar (download
  client-side a partir do markdown buscado).

### Unwanted-behavior (must-not)

- The system shall not aceitar `GET /context-pack` sem nenhum filtro de
  escopo — devolve `422 scope_required` para evitar exportar o workspace
  inteiro sem intenção explícita.
- The system shall not referenciar nenhuma empresa/organização/projeto
  específico nos textos gerados pelo bundle.

### Optional

- Where nenhum artefato é encontrado para o escopo pedido, the system may
  devolver um bundle com uma nota explícita ("nenhum requisito encontrado")
  em vez de erro — o escopo é válido, só está vazio.

## Acceptance criteria

1. [verified] `GET /context-pack?story=` devolve um Markdown com a story,
   seus CTs (corpo completo) e seus defeitos (com causa raiz/correção
   quando registradas) — verified by `backend/tests/test_context_pack.py`.
2. [verified] `GET /context-pack?epic=` inclui todas as stories daquele
   epic; `story=` restringe a uma única story mesmo dentro de um epic maior
   — verified by `backend/tests/test_context_pack.py`.
3. [verified] `GET /context-pack?squad=` inclui as decisões arquiteturais
   daquele squad — verified by `backend/tests/test_context_pack.py`.
4. [verified] `GET /context-pack` sem nenhum filtro devolve `422
   scope_required` — verified by `backend/tests/test_context_pack.py`.
5. [verified] Um escopo válido sem nenhum artefato encontrado devolve um
   bundle com nota explícita, não um erro — verified by
   `backend/tests/test_context_pack.py`.

6. [verified] `GET /context-pack?format=json` devolve `counts`/`bytes`/
   `markdown`; os toggles `testcases`/`defects`/`decisions` removem as
   respectivas seções; `last_result` anexa o último status por CT — verified
   by `backend/tests/test_context_pack.py`.
7. [verified] Com `decisions` ligado e sem `squad`, o bundle inclui as
   decisões aceitas do projeto; com `squad`, as daquele squad — verified by
   `backend/tests/test_context_pack.py`.
8. [verified] O card lista epics/stories/squads e filtra ao digitar, e o
   preview mostra contagens + Copiar/Baixar — verified by build + revisão
   visual (`frontend/src/components/AiAssist.tsx`).

## Maturity

**MVP (committed):**

- Bundle Markdown único, filtros epic/story/squad (ao menos um obrigatório)
  com pickers que listam os itens e filtram ao digitar, corpo completo de
  requisitos/CTs/decisões, defeitos com causa raiz/correção, toggles de
  seção (CTs/defeitos/decisões) + último resultado por CT, decisões em
  qualquer escopo, preview com contagens + Copiar/Baixar, e download via
  `format=json` (client-side) ou `Content-Disposition: attachment`.

**Future (aspirational, not committed):**

- Botão de export por story/epic diretamente na tela de Requisitos (hoje o
  botão vive na aba de IA).
- Filtro dos pickers também por título (hoje o `<datalist>` casa pelo ID).

## Out of scope for this spec

- Envio automático do bundle para um agente de IA externo (o usuário
  baixa/copia manualmente).
- Geração de embeddings ou indexação vetorial — o bundle é texto plano,
  quem faz RAG com ele é o agente externo.
