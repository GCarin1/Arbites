---
name: nao-passar-dados-ja-estruturados-pela-llm
description: Se a entrada JÁ está num formato estruturado (Gherkin/BDD, CSV, JSON, Markdown com âncoras), NÃO a mande para a LLM — parseie deterministicamente e preserve verbatim. LLM extrai-em-campos-e-re-renderiza, o que parafraseia, funde itens e troca campos.
when: Import/conversão em que o arquivo de origem já tem estrutura reconhecível (Feature/Scenario/Given-When-Then, colunas, chaves) e o usuário reclama que "a IA mudou/normalizou/reescreveu" o conteúdo antes de salvar.
---

# Skill — nao-passar-dados-ja-estruturados-pela-llm

## When to use this skill

- A importação manda o texto para um modelo, que devolve campos, e você
  **re-renderiza** o corpo a partir desses campos.
- Sintoma: o usuário aponta que o texto salvo difere do enviado — Feature
  trocada pelo título do cenário, "que"/artigos removidos, pontuação
  adicionada, **dois passos `And` fundidos num só**, capitalização forçada.

## Causa raiz

O pipeline "LLM extrai em schema → re-renderiza" é **intrinsecamente lossy**:
1. A LLM parafraseia ao extrair (não copia; "entende" e reescreve).
2. O schema achata a estrutura (ex.: `resultado_esperado: str` não comporta
   dois `Then/And` → eles se fundem).
3. O renderizador reconstrói com regras próprias (ex.: `Feature = title`
   quando o campo feature vem vazio).

Nenhum ajuste de prompt conserta (2) e (3): a perda é estrutural, não de
instrução.

## Procedure

1. **Detecte o formato de origem** com uma heurística barata
   (`looks_like_gherkin`: tem `Scenario:` + linha `Given/When/Then`?).
2. Se já é estruturado, **parseie você mesmo** (determinístico) e **preserve
   verbatim** — normalize só o que é cosmético e seguro (indentação), nunca as
   palavras. Reconstrua a partir das linhas originais, não de campos achatados.
3. **Não exija a LLM** nesse caminho: é mais rápido, roda offline e não
   depende de provider configurado. Reserve a LLM só para entrada realmente
   livre/desestruturada.
4. Teste com a diferença exata que o usuário mostrou (Feature preservada,
   artigos mantidos, múltiplos `And` intactos, sem pontuação injetada).

## Anti-patterns

- "Vou melhorar o prompt pra ele não reescrever" — a LLM parafraseia por
  natureza e o schema já fundiu os passos; o problema é o pipeline, não o texto.
- Re-renderizar BDD a partir de `pre_condicoes/passos/resultado_esperado`
  quando você tinha o Gherkin original em mãos.
- Mandar CSV/JSON/Markdown-com-âncoras para a LLM "normalizar".

## Related material

- `backend/arbites/ai.py` — `looks_like_gherkin`, `parse_gherkin`,
  `gherkin_body`, `gherkin_folder`.
- `backend/arbites/api.py` — branch determinístico em `/import/ai`.
- `backend/tests/test_ai_import.py`
  (`test_import_gherkin_is_preserved_verbatim_without_ai`).
- Spec `ai-assist` (#8). Relacionadas:
  [[salvar-json-truncado-de-llm]], [[modelo-de-raciocinio-content-vazio]].
