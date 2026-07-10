---
name: campos-de-referencia-com-autocomplete
description: Todo campo que referencia um item existente (id único, lista de links, ou descrição/comentário com @menção) deve usar autocomplete via GET /search em vez de <select> ou campo de id cru; e o item vinculado deve ficar visível e clicável no card.
when: Ao adicionar/editar um campo que aponta para outro artefato (story de um CT, defeito de um resultado, links de um todo, menção numa descrição/comentário) — não use <select> nem input de id cru.
---

# Skill — campos-de-referencia-com-autocomplete

## When to use this skill

- Vai criar/editar um campo que referencia outro card (CT/story/execução/
  defeito/todo): campo de id único, lista de links, ou texto livre que menciona
  um card.

## Princípio

Referência a item existente = **autocomplete**, nunca `<select>` gigante nem
campo de id cru que o usuário tem de decorar. Toda referência usa o mesmo
backend (`GET /search?q=&kinds=`) e os mesmos componentes.

## Procedure

1. **Um id só:** `SingleRefInput` (caixa de texto que sugere por id/título e
   grava o id). Filtre por tipo com `kinds` (ex.: `kinds="defect"`,
   `kinds="requirement"`). Substitui `<select>` e input de id cru.
2. **Vários ids (lista):** `LinksInput` (tokens separados por vírgula, sugere
   por token).
3. **Dentro de texto:** `MentionTextarea` — `@` dispara o autocomplete;
   descrições e **campos de comentário** que podem citar um card usam isto.
4. **Visibilidade do vínculo:** todo card mostra a que item está vinculado, e a
   menção `@ID` renderiza como **link clicável** (`mention-link`) que navega ao
   card. Vincular sem mostrar o vínculo (nem poder abri-lo) é meio caminho.
5. **Backend:** reuse `GET /search` (kinds filtra por tipo; ordena id-prefix
   primeiro). Não crie endpoint novo por campo.

## Anti-patterns

- `<select>` com todos os itens (não escala, não filtra digitando).
- Input de id cru sem sugestão (o usuário tem de saber o id de cor).
- Vincular sem exibir/linkar o item no card.

## Related material

- `frontend/src/components/Autocomplete.tsx` — `SingleRefInput`, `LinksInput`,
  `MentionTextarea`, `useSuggestions(query, kinds)`.
- `frontend/src/components/ReadView.tsx` — `mention-link` (hyperlink de `@ID`).
- `backend/arbites/api.py` — `GET /search`. Spec `todos` (autocomplete/menções).
