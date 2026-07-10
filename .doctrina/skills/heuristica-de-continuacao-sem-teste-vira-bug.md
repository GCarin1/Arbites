---
name: heuristica-de-continuacao-sem-teste-vira-bug
description: Ao escrever um parser de linhas (Gherkin, logs, markdown), não adivinhe regras de "continuação"/"comentário" (ex.:# ou aspas) sem um caso real que as exija — símbolos genéricos colidem com formatação legítima do usuário (cabeçalhos markdown, numeração) e colam texto onde não devia.
when: Escrevendo/revisando um parser linha-a-linha que decide se uma linha pertence ao item anterior (continuação) ou começa algo novo; especialmente ao adicionar suporte "só por via das dúvidas" a comentários/docstrings/tabelas sem exemplo real do formato.
---

# Skill — heuristica-de-continuacao-sem-teste-vira-bug

## When to use this skill

- Vai escrever ou revisar um `parse_*`/tokenizer linha-a-linha que precisa
  decidir "essa linha é uma continuação do item anterior, ou coisa nova?".
- Bug relatado como "está juntando coisa que não devia" / "puxou um
  comentário/cabeçalho para dentro do item errado".

## O que aconteceu aqui

Ao implementar `parse_gherkin` (verbatim import de BDD), adicionei
`line[:1] in ("|", "#", '"')` como heurística de "continuação de passo"
(tabela, docstring, comentário Gherkin) — **sem um exemplo real** que
precisasse disso. Resultado: o arquivo do usuário usava `### CTxx - título`
como separador markdown entre cenários, e essa linha (começa com `#`) foi
colada como se fosse comentário do último passo do cenário anterior.

## Procedure

1. **Só adicione uma regra de continuação com um exemplo real na mão.** Se
   você não tem um arquivo de teste que force `#`/aspas a significar
   "comentário", não escreva a regra — trate como "linha não reconhecida" e
   **ignore**, não anexe.
2. **Símbolos genéricos (`#`, `"`, `-`, `*`) são terreno compartilhado** entre
   sintaxes (markdown, comentários, citações). Uma regra baseada só no
   primeiro caractere vai colidir com formatação legítima que o usuário usa
   por outro motivo.
3. **Default seguro: linha não reconhecida = ignorada**, nunca "deve
   pertencer a alguma coisa, vou grudar no último item". Perder uma linha
   estranha é recuperável (o usuário edita); grudar errado corrompe dado.
4. Ao adicionar uma continuação de verdade (ex.: tabela Gherkin `| a | b |`),
   escreva o teste de regressão ANTES, com um exemplo puxado de um arquivo
   real do usuário — não do que "pareceria razoável" a IA prever.

## Anti-patterns

- "Vou cobrir comentário/docstring também, por garantia" sem caso de uso.
- Testar só o caminho feliz do parser e nunca um arquivo com formatação
  adjacente (cabeçalhos, numeração, notas) misturada ao conteúdo estruturado.

## Related material

- `backend/arbites/ai.py` — `parse_gherkin`.
- `backend/tests/test_ai_import.py`
  (`test_import_gherkin_ignores_markdown_headers_between_scenarios`).
- Spec `ai-assist` (#9). Relacionada:
  [[nao-passar-dados-ja-estruturados-pela-llm]] (o parser que essa regra
  quebrou foi criado por aquela mesma skill).
