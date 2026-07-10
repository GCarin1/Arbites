---
name: truncar-titulo-em-card
description: Título/texto em card de altura fixa deve truncar com line-clamp e reticências, não crescer o card — overflow-wrap sozinho quebra e expande verticalmente.
when: Ao renderizar título/rótulo dentro de um card, chip ou célula com tamanho que deve ser estável; quando um texto longo estoura/estica o container.
---

# Skill — truncar-titulo-em-card

## When to use this skill

- Um card/bloco (afazeres, KPIs, listas) tem um título e o layout deve ter
  altura previsível.
- Bug: "título grande estoura o card" / "o card cresce/estica com o texto".

## O bug (real, afazeres)

`.todo-card-title` tinha só `overflow-wrap: anywhere` — isso **quebra a palavra
mas deixa o texto fluir em N linhas**, aumentando a altura do card. O usuário
queria truncar com `…`, sem crescer.

## Procedure

1. Truncar em N linhas com reticências (mantém o card estável):
   ```css
   .title {
     display: -webkit-box;
     -webkit-line-clamp: 2;      /* nº de linhas visíveis */
     line-clamp: 2;
     -webkit-box-orient: vertical;
     overflow: hidden;
     overflow-wrap: anywhere;    /* ainda quebra tokens longos sem espaço */
     word-break: break-word;
   }
   ```
2. Para 1 linha: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`.
3. Sempre dar `title={texto}` no elemento (tooltip com o valor completo, já que
   parte fica escondida).
4. `overflow-wrap`/`word-break` sozinhos NÃO truncam — só evitam overflow
   horizontal; para não crescer é preciso `overflow: hidden` + clamp.

## Anti-patterns

- Usar `overflow-wrap: anywhere` esperando truncamento (ele só quebra linha).
- Truncar sem `title`/tooltip → o usuário perde a informação escondida.

## Related material

- `frontend/src/styles.css` — `.todo-card-title`.
- Skill relacionada: [[conteudo-longo-em-tabela-overflow]].
