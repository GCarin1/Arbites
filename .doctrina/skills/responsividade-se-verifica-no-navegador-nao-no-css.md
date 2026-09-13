---
name: responsividade-se-verifica-no-navegador-nao-no-css
description: Responsividade não se confere lendo CSS nem confiando no build — abra o app no viewport alvo e meça `scrollWidth` contra `innerWidth` tela a tela; o que quebra são sobras de layout que o CSS não denuncia.
when: Ao criar ou mexer em media query, layout de casca, grid ou qualquer coisa que precise caber numa largura menor; ao revisar "está responsivo"; antes de fechar uma change que promete tela estreita.
---

# Skill — responsividade-se-verifica-no-navegador-nao-no-css

## When to use this skill

- Você escreveu uma media query e quer saber se funcionou.
- Uma change promete "cabe no celular" e precisa provar.
- Revisão de layout que alguém declarou responsivo.

## Por que ler o CSS não basta (change 0125)

O `tsc` e o `vite build` passam com qualquer CSS — eles não sabem o que é
largura. Depois de escrever o bloco de tela estreita e ver o build verde,
abrir o navegador em 390×844 revelou **quatro** quebras que a leitura do CSS
não denunciava:

- a marca do produto quebrando em duas linhas ao lado do botão da gaveta;
- o título da página reticenciado (`Regressao do sprin…`) com metade da
  largura vazia ao lado, porque o `flex` não quebrava linha;
- o subtítulo do Health Score cortado no meio da frase por um
  `flex: 0 0 auto` que impedia o bloco de encolher;
- os títulos dos casos virando `Lo…`, `Re…`, `Se…` — indistinguíveis —
  porque a data de criação tomava o espaço que identifica o caso.

Nenhuma delas aparece no CSS: são consequências de conteúdo real dentro de
caixas reais.

## Procedure

1. **Suba o app de verdade** com dados semeados pela API (um ciclo, casos
   com títulos longos, resultados variados). Layout com lista vazia não
   quebra — e é justamente a lista cheia que quebra.
2. **Meça o transbordo por tela**, que é o teste objetivo:
   ```js
   const m = await page.evaluate(() => ({
     doc: document.documentElement.scrollWidth, win: window.innerWidth,
   }));
   // doc > win  =>  a página rola para o lado: quebrou
   ```
3. **Percorra as telas densas**, não a inicial: repositório em árvore,
   quadro de colunas, dashboard de cartões, formulário longo, e o menu que
   abre no canto (ele sangra pela direita).
4. **Olhe as capturas.** O passo 2 acha transbordo; só o olho acha texto
   ilegível, reticências cedo demais e rótulo cortado. Os dois passos são
   necessários e nenhum substitui o outro.
5. **Confirme que o desktop não regrediu**, no mesmo script: a media query
   erra para os dois lados, e o layout largo é o que já funcionava.
6. **Ponteiro grosseiro é `pointer: coarse`, não largura** — um tablet largo
   também é tocado, e alvo de toque é sobre dedo, não sobre pixels.

## Mecânica neste ambiente

O Chromium pré-instalado pode ser de build diferente da que o Playwright
recém-instalado espera; aponte o executável em vez de baixar outro:

```js
chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' })
```

Para o app, semeie o estado pela API antes de abrir o navegador — o fluxo de
login com troca de senha obrigatória atrapalha a automação e não é o que se
está testando.

## Anti-patterns

- Declarar responsivo porque o build passou.
- Testar só a tela inicial, que costuma ser a mais simples do produto.
- Medir só o transbordo e não olhar a captura (`Lo…` cabe na largura).
- Media query por largura para alvo de toque.

## Related material

- `.doctrina/changes/archive/2026-09-13-0125-visao-mobile-casca-app/`
- `frontend/src/styles.css` — o bloco `@media (max-width: 860px)` e o
  `@media (pointer: coarse)`.
