# Change 0193-exportacao-carregamento-nenhum-sinal — o clique que não respondia

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** design-system

## Why

Exportar 30 dias de painel em PDF leva alguns segundos, e a tela não dizia
nada. O clique não mudava nada visível: quem clicou não sabe se o pedido
saiu, se está indo, ou se o botão não funcionou. A reação natural é clicar de
novo — que é o pior desfecho, porque agora são dois PDFs sendo gerados.

E as telas que ainda não têm dado mostravam "Carregando…" centralizado numa
página em branco, que não diz o que vem depois e faz tudo saltar de posição
quando o dado chega.

## What

- `frontend/src/components/Progresso.tsx`: `Progresso` (barra determinada
  quando há `Content-Length`, **indeterminada** quando não há — inventar
  porcentagem seria mentir) e `Esqueleto`.
- `api.observabilityBaixar()`: o download vira fetch lido em pedaços, com a
  fração informada a cada pedaço, e o arquivo salvo com o nome que o servidor
  sugeriu em `Content-Disposition`.
- Os três botões de export desabilitam durante a geração, e a barra ocupa uma
  linha própria do cabeçalho.
- Painel e Evidências passam a mostrar esqueleto.
- `prefers-reduced-motion`: sem animação; a barra continua informando pela
  largura e pelo texto.

## Scope boundaries

A barra cobre a exportação. A busca de execuções continua com o rótulo
"Buscando…": informar progresso real dela exigiria streaming do backend, que
é outra mudança.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] The affected spec's acceptance criteria are met and cite their evidence.
- [x] `backend/tests/test_export_progresso.py`: 9 testes — tamanho e nome de
      arquivo nos quatro formatos, e o período sem dado.
- [x] Navegador: o PDF baixou como `observabilidade-2026-09-17.pdf`, a barra
      apareceu com os botões desabilitados, e nenhum erro de página.
- [x] `audita-estreito.mjs` em 390px: 15 telas, nenhum achado.

## Open questions

Nenhuma.
