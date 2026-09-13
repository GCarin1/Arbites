# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

---

Duas coisas da mesma família, provadas no mesmo lugar.

**A escala de espaçamento tem um buraco.** Ela começa em 8px, e tudo que é
menor que isso passou a ser inventado caso a caso. Contado no `styles.css`:
29 usos de `6px`, 29 de `4px`, 11 de `10px`, 11 de `2px`, mais `3px` e `5px`
— 87 valores fora de qualquer escala, cada um decidido no calor do momento.
O token existe para que a decisão seja tomada uma vez; sem degrau abaixo de
8px, ele só empurrou a decisão para o CSS de cada componente.

**Não há controle de densidade.** Este é um produto que vive de tabela e de
árvore, e a mesma tela serve a duas perguntas opostas: "quantos casos existem
neste ciclo" (quero ver quarenta de uma vez) e "o que diz este caso" (quero
ler sem apertar os olhos). Hoje só existe uma resposta, fixa.

A densidade muda o que determina quantas linhas cabem — o respiro das linhas
e a altura dos controles. Não mexe na separação entre seções, que é
estrutura, não conforto: encolher o espaço entre blocos não faz caber mais
nada, só embaralha a leitura. E não desce abaixo do alvo de toque num
ponteiro grosseiro, porque o dedo não encolhe junto.

```ops
bump-version minor
append-requirement ubiquitous: The system shall oferecer degraus de espaçamento de 4px e 12px na escala de tokens, para que não haja valor de espaçamento decidido fora dela.
append-requirement ubiquitous: The system shall oferecer três densidades de leitura — compacta, padrão e confortável — que alteram o respiro das linhas e a altura dos controles, preservando a separação entre seções.
append-requirement ubiquitous: The system shall guardar a densidade escolhida no navegador de quem escolheu, por ser preferência de leitura de uma pessoa num aparelho, e não configuração do workspace.
append-requirement unwanted: The system shall not deixar a densidade compacta reduzir um alvo interativo abaixo do mínimo de toque quando o ponteiro for grosseiro.
append-criterion [unverified] As três densidades mudam quantas linhas cabem na mesma altura de tela, e a compacta não reduz nenhum alvo de toque abaixo do mínimo — verified by `frontend/src/styles.css` + `frontend/src/components/Profile.tsx`.
append-criterion [unverified] A escala de espaçamento cobre os degraus usados pela interface, e a densidade escolhida sobrevive ao recarregamento da página — verified by `frontend/src/styles.css` + `frontend/src/components/Profile.tsx`.
```
