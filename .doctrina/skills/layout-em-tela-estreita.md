---
name: layout-em-tela-estreita
description: Conferir layout estreito medindo `scrollWidth` da PÁGINA não pega quase nada — texto cortado dentro do cartão, rótulo escrito por cima do valor, filho cortado pelo ancestral e alvo de toque abaixo de 24px passam todos por baixo desse número; rode `frontend/scripts/audita-estreito.mjs` e trate cada família de achado com o padrão já existente no repo.
when: O agente vai criar ou alterar qualquer tela, cartão, tabela ou controle do frontend, ou foi chamado para revisar/consertar layout em telefone.
---

# Skill — layout em tela estreita

## When to use this skill

- Qualquer alteração em `frontend/src/components/*.tsx` ou em `styles.css`
  que acrescente tabela, cartão, faixa de filtros, gráfico ou link.
- O relato é "quebrou no mobile", "texto cortado", "não consigo clicar".
- Antes de fechar uma change que tenha UI — a 390px, não só a 1440px.

## Procedure

0. **Reconstrua o frontend antes de conferir qualquer coisa.**
   `frontend/dist/` não é versionado: sem `npm --prefix frontend run build` o
   servidor entrega o bundle anterior, e você vai medir a tela errada. O
   `serve` avisa no arranque (change 0182), mas o hábito é seu.

1. Suba a aplicação e rode o detector nas duas larguras que importam:

   ```
   node frontend/scripts/audita-estreito.mjs \
     --url http://127.0.0.1:8000 --email <admin> --senha <senha> --largura 390
   node frontend/scripts/audita-estreito.mjs ... --largura 320
   ```

   Ele sai com código 1 se achar algo, então serve de gate. Playwright não é
   dependência do projeto: aponte uma instalação com `PLAYWRIGHT_ROOT`.

2. Se a tela é nova, acrescente-a à lista `TELAS` do script. Uma tela que o
   detector não visita é uma tela sem revisão.

3. Trate por família de achado, usando o padrão QUE JÁ EXISTE aqui:

   | achado | causa típica | o que fazer |
   | --- | --- | --- |
   | `passa-da-viewport` numa `<table>` | falta a classe que empilha | `className="dense stack-narrow"` **e** `data-label` em cada `<td>` |
   | `texto-cortado` | `text-overflow: ellipsis` + `white-space: nowrap` | deixar quebrar em `@media (max-width: 720px)` |
   | `cortado-pelo-ancestral` | filho maior que o cartão | `overflow-wrap: anywhere`, ou `.scroll-x` no container |
   | `alvo-pequeno` | botão com `height: auto` herdando a linha de texto | `padding-block: 4px` na média estreita, ou `min-height: 24px` |
   | `rotulo-sobre-o-valor` | `white-space: nowrap` herdado, ou fonte mono no rótulo | `white-space: normal` + `overflow-wrap: anywhere` no `::before`, e `font-family: var(--font-ui)` — rótulo é cromo, não dado |

4. Se você acrescentou uma checagem ao detector, **prove que ela pega**:
   reintroduza a causa por CSS injetado (`page.addStyleTag`) e confira que o
   achado aparece, depois remova. Checagem que nunca viu o defeito para o qual
   foi escrita é esperança, não teste.

5. Confira o resultado com um print de verdade, e AMPLIADO
   (`deviceScaleFactor: 3` e print só do elemento). O detector não vê feiura,
   vê quebra — e num print de 390px em escala 1 dois textos sobrepostos
   parecem só um borrão de renderização.

## Anti-patterns

- **Medir `document.documentElement.scrollWidth - innerWidth` e declarar a
  tela responsiva.** Foi o que estas telas passaram durante várias changes
  enquanto quebravam: a página não estoura quando o pai tem
  `overflow: hidden` — a frase é que some dentro do cartão.
- **Escrever `data-label` nas células e esquecer `stack-narrow`.** A classe é
  o opt-in; sem ela os rótulos ficam no HTML sem efeito nenhum e a tabela rola
  de lado. Aconteceu em três tabelas da Observabilidade de uma vez.
- **Crescer a área de acerto com um `::after` invisível num alvo DENSO.** Com
  os pontos a poucos pixels um do outro, a área invisível do vizinho passa por
  cima e rouba o toque do alvo visível — fica pior que antes. Área de acerto
  resolve alvo isolado; alvo denso precisa de ESPAÇO (largura mínima
  proporcional à quantidade, dentro de um container que rola).
- **Comparar o elemento com o PAI imediato para decidir se ele está cortado.**
  Um gráfico pode ser mais largo que seu wrapper e ainda caber no cartão. Quem
  corta é o primeiro ancestral com `overflow` diferente de `visible`.
- **Confiar só no retângulo.** Rótulo de célula empilhada é texto de
  `::before`: a CAIXA continua com a largura da faixa e o TEXTO escapa por
  cima do valor. Nenhuma medida de `getBoundingClientRect` pega isso — mede-se
  a largura natural do texto com a fonte do pseudo-elemento.
- **Conferir sem reconstruir.** Um defeito que "continua lá" depois do
  conserto quase sempre é o `dist` antigo. Antes de reabrir a investigação,
  confirme que o build é mais novo que o código.
- **Silenciar um achado no detector.** Se um alvo pequeno é aceitável, a
  exceção se declara no elemento (`data-alvo-pequeno="equivalente: ..."`), com
  o caminho equivalente escrito ali. Quem declara assume; quem lê o markup vê
  a justificativa. Esconder no script faz a próxima pessoa reintroduzir o
  defeito sem saber.

## Related material

- `frontend/scripts/audita-estreito.mjs` — o detector.
- `.doctrina/changes/archive/2026-09-16-0181-revisao-layout-tela-estreita/`
- `.doctrina/skills/responsividade-se-verifica-no-navegador-nao-no-css.md` —
  esta skill é o método que faltava àquela.
- `.doctrina/skills/botao-como-item-de-lista-heranca-justify.md` — o estilo
  base de `button` interfere em todo controle novo.
- [Workflow](../../docs/en/workflow.md)
