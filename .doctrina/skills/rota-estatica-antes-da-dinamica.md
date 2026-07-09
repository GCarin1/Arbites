---
name: rota-estatica-antes-da-dinamica
description: No FastAPI/Starlette, rotas estáticas (/x/folders) devem ser registradas ANTES das dinâmicas (/x/{id}) — senão o path param captura o segmento fixo e devolve 404.
when: Ao adicionar uma rota com segmento fixo sob um prefixo que já tem rota com path param (ex.: /testcases/{id} existente e nova /testcases/folders), ou ao depurar um 404 em rota que "existe".
---

# Skill — rota-estatica-antes-da-dinamica

## When to use this skill

- Vai adicionar `GET|POST|DELETE /<coisa>/<segmento-fixo>` num router que já tem
  `/<coisa>/{param}` (o padrão dos CRUDs deste projeto).
- Um endpoint novo devolve **404 com detalhe de "não encontrado" da entidade**
  (ex.: `folders não encontrado`) — sinal de que o path param engoliu o segmento.

## O bug (real, change do repositório de test cases)

`DELETE /testcases/folders` foi registrado **depois** de
`DELETE /testcases/{entity_id}`. O roteador casa na ordem de registro, então
"folders" virou `entity_id`, `_find_path` não achou e devolveu 404 — parecia
"rota não existe", mas era captura pelo param dinâmico.

## Procedure

1. Registre rotas com segmento **fixo** antes das rotas com **path param** do
   mesmo prefixo e método. No arquivo, mova o bloco para cima da rota dinâmica
   e deixe um comentário explicando a ordem.
2. Teste o caso que colide: chame a rota estática e assegure que NÃO devolve o
   404 da entidade (`test_folder_create_move_and_delete` fez exatamente isso).
3. Alternativa quando a ordem não é controlável: renomeie para não colidir
   (ex.: `/tc-folders`) — mas prefira a ordem correta.

## Anti-patterns

- Adicionar rota estática "no fim do arquivo" por conveniência, sob um prefixo
  que tem `{param}` no mesmo método.
- Diagnosticar o 404 como "backend desatualizado" sem checar colisão de rota.

## Related material

- `backend/arbites/api.py` — bloco "repositório de pastas" (comentário de ordem).
