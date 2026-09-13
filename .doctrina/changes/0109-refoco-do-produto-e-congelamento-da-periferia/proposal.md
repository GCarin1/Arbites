# Change 0109-refoco-do-produto-e-congelamento-da-periferia — Refoco do produto e congelamento da periferia

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (confident; signals: registrar)
- **Affects specs:**

## Why

Estreitar o produto ao que ele e de fato: repositorio versionado de casos de teste, ciclo e execucao, com IA como ajuda. Congelar as capabilities que sairam do foco declarado — reunioes, daily, decisoes, memoria de projeto, mapa de risco, migracao Xray e as duas de automacao — marcando as specs como deprecated sem remover codigo nem rota, para nao destruir dado de quem ja usou. Enterrar businessmap, que nunca foi construida. Manter afazeres por decisao explicita do usuario. Registrar no product.md que SC5 e SC6 foram entregues e sairam de foco.

## What

- ADR 0012 — o recorte do produto: núcleo, infraestrutura, congelado,
  enterrado, e o significado preciso de "congelado".
- 8 deltas MODIFIED marcando `Status: deprecated` e
  `Implementation: frozen` em `meetings`, `daily`, `decisions`,
  `project-memory`, `risk-map`, `xray-migration`, `local-automation` e
  `ci-automation`.
- 1 delta REMOVED em `businessmap`, que nunca saiu de `planned`.
- `product.md`: bloco de foco ativo na Vision; SC5 e SC6 marcados como
  entregues-e-congelados; SC10 removido junto com a capability; Businessmap
  passa de "adiada" para "abandonada".
- `frontend/src/App.tsx`: grupos de navegação reorganizados por foco, com
  "Mais" reunindo o congelado e nascendo recolhido; itens congelados
  marcados visualmente e com tooltip.
- Referências a uma empresa específica removidas do `product.md` e da spec
  `ci-automation` — o produto é genérico.

## Scope boundaries

- **Nenhuma linha de código de capability congelada é removida.** Rotas
  continuam respondendo, telas continuam abrindo, testes continuam no gate.
  O que muda é a posição na navegação e o compromisso de investimento.
- Nenhum dado de usuário é tocado: quem registrou reuniões, dailies e
  decisões continua com tudo.
- A `businessmap` é a única exclusão de fato, e só porque nunca existiu
  fora da spec.
- O reagrupamento da navegação aqui é o mínimo. A barra superior e o avatar
  são o 0110.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] `python -m pytest backend/tests -q` passa **sem nenhuma alteração de
      teste** — a prova de que congelar não quebrou nada é a suíte das áreas
      congeladas continuar verde.
- [ ] `npm --prefix frontend run build` passa.
- [ ] `doctrina validate` sem erros após marcar 8 specs como deprecated e
      remover uma.
- [ ] `doctrina trace` não reporta âncora órfã depois da saída do SC10.

## Open questions

Nenhuma. O recorte foi definido pelo autor e está registrado na ADR 0012,
inclusive a exceção de `todos`, que fica no escopo ativo por decisão
explícita apesar de não pertencer ao núcleo.
