---
name: keyword-match-descarta-frontmatter-antes-de-tokenizar
description: Uma função de casamento por palavra-chave (keyword match) que recebe o arquivo INTEIRO de um documento (frontmatter YAML + corpo) e limita quantas palavras extrai (ex.: [:8]) pode ter esse orçamento inteiro consumido por metadados (id/title/kind/status) antes de alcançar o conteúdo real — resultado: nunca casa nada, sem erro, sem log.
when: Ao escrever/revisar uma função que extrai palavras-chave de um texto para busca/match (ex.: sugestão de duplicata, cruzamento de lições aprendidas, RAG simples por keyword) e o texto de entrada pode ser um arquivo com frontmatter YAML.
---

# Skill — keyword-match-descarta-frontmatter-antes-de-tokenizar

## When to use this skill

- Vai escrever uma função `find_similar`/`find_relevant_*` que extrai
  palavras-chave (`re.findall(r"\w{4,}", text)`) de um texto para comparar
  contra outros registros (busca por palavra em comum).
- O texto de entrada PODE ser o conteúdo bruto de um arquivo com frontmatter
  (`---\nid: ...\ntitle: ...\n---\n\ncorpo real aqui`), não só texto livre.

## O bug (real, encontrado neste projeto)

`find_relevant_lessons(conn, text)` extraía as primeiras 8 palavras de 4+
letras de `text` para buscar defeitos relacionados. Funcionava perfeitamente
no teste unitário (texto livre direto). Na integração real, `text` era o
ARQUIVO INTEIRO da story lido do disco — frontmatter YAML + corpo:

```
---
id: ST-0001
title: Cadastro de cliente
kind: story
status: draft
---

Como usuário, quero que o cadastro exija validação obrigatória...
```

As primeiras 8 palavras de 4+ letras são `0001, title, cadastro, cliente,
kind, story, status, draft` — **inteiramente do frontmatter**. O conteúdo
real ("validação", "obrigatória", os termos que importam) nunca é alcançado.
O orçamento acaba antes do corpo começar. **Nenhum erro, nenhum log — a
função só nunca encontra nada**, e só aparece testando a integração de ponta
a ponta com um documento realista (frontmatter + corpo), não com texto puro.

## Procedure

1. **Descarte o frontmatter YAML antes de tokenizar:**
   `re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)`.
2. **Deduplique as palavras** (`dict.fromkeys(...)`) antes de cortar pelo
   limite — um texto repetitivo não deve desperdiçar o orçamento com a mesma
   palavra várias vezes.
3. **Use um limite generoso** (dezenas, não um punhado) — o custo é só mais
   algumas queries `LIKE`, e um limite apertado é o que causa o bug em
   primeiro lugar quando há QUALQUER ruído antes do conteúdo relevante.
4. **Teste com um documento REALISTA**, não só com a string de conteúdo já
   extraída à mão — o teste unitário da função em isolamento pode passar
   perfeitamente enquanto a integração real está quebrada, exatamente porque
   o teste isolado nunca reproduziu o frontmatter.

## Anti-patterns

- Testar a função de keyword-match só com texto já "limpo" (sem frontmatter),
  quando na integração real ela sempre recebe o arquivo bruto.
- Um `[:N]` pequeno logo após o `re.findall`, sem considerar que os
  primeiros tokens de um DOCUMENTO ESTRUTURADO costumam ser metadados, não
  conteúdo.
- Assumir "a função está certa porque o teste unitário passa" sem um teste
  de integração que usa a mesma forma de texto que o código de produção
  realmente passa pra ela.

## Related material

- `backend/arbites/ai.py` — `find_relevant_lessons` (strip de frontmatter),
  `find_similar` (mesmo limiar de 4 letras, sem esse problema porque só
  recebe `title`, não o arquivo inteiro).
- `backend/tests/test_lessons_learned.py` —
  `test_generate_testcases_injects_relevant_lessons_into_prompt` (teste de
  integração que usa `story["id"]`, forçando o caminho que lê o arquivo
  inteiro do disco — foi o que expôs o bug).
