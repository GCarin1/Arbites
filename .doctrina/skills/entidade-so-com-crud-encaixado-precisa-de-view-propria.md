---
name: entidade-so-com-crud-encaixado-precisa-de-view-propria
description: Uma entidade com API CRUD completa (GET/POST/PUT) mas cuja UNICA porta de entrada na UI é um modal aninhado dentro de outro fluxo (ex.: "criar defeito a partir de um resultado de execução") não tem gerenciamento de verdade — falta listar/editar/excluir fora daquele contexto específico.
when: Ao avaliar se uma entidade do domínio precisa de uma página/aba própria — sinal de alerta é "só existe um Modal de criação embutido em outra tela" e nenhuma navegação (@MENÇÃO, link) consegue abrir o item existente.
---

# Skill — entidade-so-com-crud-encaixado-precisa-de-view-propria

## When to use this skill

- Usuário relata "não tem lugar pra gerenciar X" para uma entidade que já
  tem rotas de API completas.
- Ao auditar o código, a única forma de criar/ver X na UI é um modal aberto
  de dentro de outro fluxo (ex.: `NewDefectModal` só abria a partir de um
  resultado `failed` numa execução).

## Sinais de que falta uma view dedicada

1. **API tem CRUD, UI não tem lista.** `GET /X`, `POST /X`, `PUT /X/{id}`
   existem, mas a única tela que os usa é um formulário de criação embutido
   em OUTRO fluxo — não há onde ver todos os X, filtrar, editar um já
   existente fora daquele contexto, ou excluir.
2. **Navegação por menção/link está com um comentário "sem view dedicada".**
   Se o código de navegação (`navigateTo`/`onMention`) tem um `if` faltando
   ou um comentário explícito dizendo que aquele prefixo de ID não navega
   pra lugar nenhum, é o sintoma mais direto — a entidade existe no domínio
   mas é invisível na navegação.
3. **Falta rota GET singular e/ou DELETE.** Ao construir a view, muitas
   vezes descobre-se que faltava `GET /X/{id}` (pra edição, já que a
   listagem costuma omitir campos pesados como corpo/descrição) e/ou
   `DELETE /X/{id}` (pra corrigir engano) — completar o CRUD é parte do
   trabalho, não só a tela.

## Procedure

1. Confirme a lacuna checando a navegação primeiro (busque
   `// <ENTIDADE> não tem view dedicada` ou equivalente) — é o ponto exato
   onde alguém já documentou a lacuna sem preencher.
2. Reuse o padrão de UMA entidade irmã já bem resolvida no mesmo app (lista
   flat + filtro + modal de criar/editar + confirmação de excluir) em vez de
   inventar um layout novo — procure a entidade estruturalmente mais
   parecida (flat, sem hierarquia de pastas) e copie a forma.
3. Complete o CRUD que faltar no backend (tipicamente `GET /{id}` singular
   e `DELETE /{id}`) ANTES de montar a tela — a UI vai precisar dos dois.
4. Ligue a navegação por menção/link (`@PREFIXO-XXXX`) à nova aba, abrindo
   o editor já preenchido — não só troque de aba e deixe o usuário procurar.
5. Reuse esquemas de cor/campo já estabelecidos alhures no app (ex.: mapa de
   cor por severidade já usado num dashboard) em vez de inventar um novo.

## Anti-patterns

- Construir uma tela nova do zero sem checar se já existe um padrão de lista
  flat + modal no mesmo código pra copiar.
- Deixar `DELETE` de fora "porque a entidade normalmente não é excluída" —
  gerenciar inclui corrigir enganos; sem exclusão o usuário fica preso a
  registros criados errado.
- Adicionar a tela sem também conectar a navegação por menção/link — a
  entidade fica alcançável só pelo menu, não pelas referências cruzadas que
  o resto do app já usa.

## Related material

- `frontend/src/components/Defects.tsx` — nova view; `frontend/src/components/Todos.tsx`
  foi o template estrutural copiado (lista flat + modal + confirmação).
- `backend/arbites/api.py` — `GET /defects/{id}`, `DELETE /defects/{id}`
  (faltavam apesar do resto do CRUD já existir).
- `frontend/src/App.tsx` — `navigateTo` (ramo `DF-XXXX` que antes só tinha
  o comentário "sem view dedicada").
- Spec `defects` (#5).
