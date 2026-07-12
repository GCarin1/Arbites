# Change 0052-banco-de-licoes-aprendidas-defeitos-ganham-3-cam — Banco de Licoes Aprendidas: defeitos ganham 3 campos opcionais (root_cause, fix, prevention). GET /defects?has_lesson=true filtra os que tem licao preenchida; GET /defects/{id} ja retorna. UI: badge 'licao' na lista, filtro checkbox, secao dedicada no modal de editar/criar defeito. Cruzamento com IA: find_relevant_lessons faz keyword-match (sem embeddings) entre o texto da story e causa/prevencao de defeitos com licao preenchida; generate_testcases injeta as licoes relevantes no prompt (nao repetir o mesmo bug) e a resposta expoe lessons_used para o usuario ver o que foi considerado

- **Status:** proposed
- **Date:** 2026-07-12
- **Owner:**
- **Affects specs:** defects, ai-assist

## Why

Banco de Licoes Aprendidas: defeitos ganham 3 campos opcionais (root_cause, fix, prevention). GET /defects?has_lesson=true filtra os que tem licao preenchida; GET /defects/{id} ja retorna. UI: badge 'licao' na lista, filtro checkbox, secao dedicada no modal de editar/criar defeito. Cruzamento com IA: find_relevant_lessons faz keyword-match (sem embeddings) entre o texto da story e causa/prevencao de defeitos com licao preenchida; generate_testcases injeta as licoes relevantes no prompt (nao repetir o mesmo bug) e a resposta expoe lessons_used para o usuario ver o que foi considerado

## What

Primeira das 6 ideias do "documento de memória de projeto/IA". Cada defeito
ganha uma lição aprendida opcional (causa raiz/correção/prevenção); meses
depois, ao gerar CTs para uma feature parecida, a IA já entra sabendo do bug.

- **backend/arbites/indexer.py** — `defects` ganha `root_cause`/`fix`/
  `prevention` (CREATE + `ALTER TABLE` tolerante, mesmo padrão das migrações
  anteriores — índice descartável, mas upgrade sem exigir apagar o `.db`);
  `_insert_defect` lê os 3 campos do frontmatter.
- **backend/arbites/api.py** — `DefectIn`/`DefectUpdate` aceitam os 3 campos;
  `GET /defects?has_lesson=true`.
- **backend/arbites/ai.py** — `find_relevant_lessons(conn, text, limit=3)`:
  casamento por palavra-chave (≥4 letras, sem repetição, cap 40) contra
  título/causa/prevenção de defeitos com lição preenchida — sem embeddings,
  determinístico, funciona 100% sem IA (a lição já é buscável na UI; isto só
  a injeta no prompt). Bug encontrado e corrigido no processo: `text` é o
  ARQUIVO INTEIRO da story (frontmatter + corpo) — sem descartar o
  frontmatter YAML antes de tokenizar, o orçamento de palavras era consumido
  inteiro por "title"/"kind"/"status"/"draft" e a lição nunca casava. Fix:
  `re.sub` remove o bloco `---
...
---
` antes de extrair palavras.
  `generate_testcases` aceita `lessons` opcional e injeta um bloco no system
  prompt ("não repita a mesma causa").
- **`POST /ai/generate-testcases`** busca lições relevantes antes de chamar o
  provider e devolve `lessons_used` (id+título) na resposta.
- **frontend/src/components/Defects.tsx** — filtro "Só com lição aprendida",
  badge na listagem, seção "Lição aprendida" no modal (3 campos opcionais).
- **frontend/src/components/AiAssist.tsx** — mostra "considerou N lição(ões)
  aprendida(s): DF-x, DF-y" quando a geração usou alguma — visibilidade de
  que a IA está realmente usando o histórico, não é uma promessa vazia.
- **defects spec** MODIFIED (delta, #6); **ai-assist spec** MODIFIED
  (delta, #10).

## Scope boundaries

- Casamento por PALAVRA-CHAVE, não semântico — sem embeddings/RAG. Acrônimos
  curtos (CPF, CEP — 3 letras) ficam de fora do limiar de 4 letras (mesmo
  limiar já usado em `find_similar` para duplicidade de CT); anotado como
  limitação conhecida, não resolvido aqui para não introduzir uma lista de
  stopwords sem necessidade comprovada.
- Não cria uma página "Banco de Lições" separada — reusa a listagem de
  Defeitos com filtro, evitando duplicar UI de lista.
- Cruzamento de lições é usado hoje só em `generate-testcases`; `review`/
  `negative-cases` ficam de fora desta rodada (mesma mecânica, extensível
  depois se fizer sentido).

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] `doctrina verify` verde (159 testes backend + build frontend).
- [x] Critério #6 do defects e #10 do ai-assist citam `backend/tests/test_lessons_learned.py`.

## Open questions

<!-- List unresolved decisions. Empty if none. -->
