---
name: lista-vazia-nao-e-sem-filtro
description: Num filtro multi-seleção serializado como string (CSV em query param), a seleção VAZIA e a ausência de filtro colapsam no mesmo valor "" — a UI deve tratar seleção vazia localmente (mostrar nada) em vez de mandar "" e receber tudo.
when: O agente está implementando ou revisando um filtro multi-seleção (checkboxes, chips) cujo estado vira um parâmetro de query serializado (join por vírgula) para uma API onde o parâmetro vazio significa "sem filtro".
---

# Skill — lista-vazia-nao-e-sem-filtro

## When to use this skill

- O agente está criando checkboxes/chips de filtro cujo estado é
  `string[]` e vira `?tipos=a,b,c` na chamada de API.
- O backend do endpoint interpreta o parâmetro vazio/ausente como "todos"
  (padrão comum: `[k for k in param.split(",") if k] or None`).

## Procedure

1. Identifique a colisão: `[].join(",")` === `""` === "usuário não filtrou
   nada". Dois estados de intenção OPOSTOS (quero nada × quero tudo)
   produzem a mesma requisição.
2. Resolva na UI, antes da chamada: se a seleção está vazia, curto-circuite
   com resultado vazio local (`setItems([]); return;`) — não chame a API.
   Deixe um comentário explicando por quê (o `""` no backend significa "sem
   filtro", não "nenhum").
3. Alternativa quando a semântica de API é sua: use um valor sentinela
   explícito (`?tipos=none`) ou distinga parâmetro ausente de parâmetro
   vazio no backend — mas só se puder mudar o contrato; o curto-circuito na
   UI não exige mudança de API.
4. Teste manual obrigatório do caso: desmarcar TODOS os itens do filtro e
   confirmar que a lista fica vazia (não cheia).

## Anti-patterns

- `api.memoryTimeline(kinds.join(","))` com `kinds = []` → backend recebeu
  `kinds=""` → devolveu a timeline INTEIRA. Desmarcar todos os filtros da
  Memória do Projeto mostrava tudo em vez de nada (bug real, change 0059).
- "Consertar" forçando pelo menos um checkbox sempre marcado — muda a UX
  para esconder o bug em vez de tratar o estado.

## Related material

- `frontend/src/components/Memory.tsx` — curto-circuito no `load()`.
- `.doctrina/specs/project-memory/spec.md` — Unwanted-behavior sobre o
  filtro vazio.
- `.doctrina/changes/archive/2026-07-13-0059-fix-varredura-de-inconsistencias-entre/`
