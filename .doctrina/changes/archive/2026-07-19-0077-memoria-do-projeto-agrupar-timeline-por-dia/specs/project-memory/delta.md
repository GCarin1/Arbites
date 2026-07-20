# Delta — project-memory (change 0077)

**Operation:** MODIFIED

Recorte por período e agrupamento por dia na linha do tempo. O conteúdo já
foi mesclado direto em `.doctrina/specs/project-memory/spec.md` (deltas
prose, merge manual — ver skill de quirks do doctrina).

## MODIFIED — Requirements (EARS)

### Ubiquitous (adicionar)

- The system shall aceitar em `GET /memory/timeline` os parâmetros opcionais
  `date_from` e `date_to` (`YYYY-MM-DD`, inclusivos), recortando os eventos
  de TODAS as fontes pelo prefixo de data de `at` antes do corte por
  `limit`. [unverified]
- The system shall expor `GET /memory/timeline/years?kinds=` devolvendo, em
  ordem decrescente, os anos distintos que têm ao menos um evento (UNION
  sobre as colunas de data das mesmas fontes), para popular o seletor de ano
  com dados reais. [unverified]

### State-driven (adicionar)

- While a aba Memória está aberta, the system shall agrupar os eventos por
  DIA em cabeçalhos colapsáveis (data + contagem), com os dias mais recentes
  expandidos e os antigos colapsados, e oferecer controles combináveis de
  Ano, Mês, tipos e busca textual (a busca filtra client-side por
  id/título/resumo; Ano/Mês viram `date_from`/`date_to`). [unverified]

## Acceptance criteria (append)

9. [unverified] `GET /memory/timeline` com `date_from`/`date_to` recorta os
   eventos ao período em todas as fontes, e `GET /memory/timeline/years`
   lista os anos com eventos em ordem decrescente — verified by
   `backend/tests/test_project_memory.py`.
10. [unverified] A aba agrupa a timeline por dia colapsável e os filtros
    Ano/Mês/tipos/busca combinam — verified by build + revisão visual
    (`frontend/src/components/Memory.tsx`).
