# Tasks — Change 0052

- [x] Backend: schema `defects` ganha `root_cause`/`fix`/`prevention` (CREATE + migração ALTER tolerante).
- [x] Backend: `_insert_defect` lê os 3 campos do frontmatter; `DefectIn`/`DefectUpdate` os aceitam.
- [x] Backend: `GET /defects?has_lesson=true`; `create_defect` grava os 3 campos.
- [x] Backend: `ai_ops.find_relevant_lessons(conn, text, limit=3)` — keyword-match (≥4 letras,
      dedup, cap 40) em causa/prevenção/título de defeitos com lição preenchida; strip de
      frontmatter YAML antes de tokenizar (senão o budget de palavras é consumido por metadados).
- [x] Backend: `generate_testcases` aceita `lessons` opcional e injeta bloco no system prompt;
      `POST /ai/generate-testcases` busca lições relevantes e devolve `lessons_used`.
- [x] Frontend: `Defect` type + `GeneratePreview.lessons_used`; `Defects.tsx` — filtro "Só com
      lição aprendida", badge na lista, seção "Lição aprendida" no modal (causa/correção/prevenção).
- [x] Frontend: `AiAssist.tsx` mostra quantas lições foram consideradas na geração.
- [x] Testes (persistência, filtro, keyword-match isolado, injeção no prompt real via mock
      transport, ausência de match) + suíte verde (159) + build.
- [x] Smoke HTTP real (criar defeito com lição → listar filtrado → GET individual).

## Closing steps

- [x] Apply: merge deltas nas specs defects + ai-assist.
- [x] Archive.
- [x] Update index.json.
