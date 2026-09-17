# Change 0196-mudou-testes-instaveis-topo — notícia depois do estado

- **Status:** applied
- **Applied:** 2026-09-17
- **Date:** 2026-09-17
- **Owner:** Gcarini
- **Lane:** runtime
- **Affects specs:** ci-automation

## Why

*"A seção 'o que mudou' e 'testes instáveis' estão no início da página, está
ruim, joguei para o final."*

As duas abriam a aba e empurravam para baixo os números que se consulta todo
dia. Quem entra para ver "como estamos" não entra para ler uma lista de
exceções — notícia vem **depois** do estado, não antes.

E veio junto uma pergunta que a tela não respondia: *"o que faz eles
instáveis? Nas próximas rodadas eles podem não estar instáveis, mas continuam
sendo indicados como instáveis, certo?"*

**Errado, e é uma boa notícia** — a lista já era recalculada a cada período,
então um cenário que para de balançar some dali sozinho. Só que nada na tela
dizia isso, e um rótulo que parece grudar muda completamente como se lê a
lista.

## What

- "O que mudou" e "Testes instáveis" passam para o fim da aba.
- A explicação da instabilidade passa a dizer: o **período** exato que a
  produziu, o **critério** (passou e falhou dentro do mesmo período), que a
  lista é **recalculada** a cada período, e o que "viradas" mede.

## Scope boundaries

O cálculo não muda — ele já estava certo. O que muda é a ordem e o que a tela
conta sobre ele.

## Verification

- [x] Automated checks pass (`doctrina verify`).
- [x] `frontend/scripts/audita-ordem.mjs`: a ordem esperada confere no
      DOM — indicadores, pizzas, sinais, Onde doer, O que mudou.

## Open questions

Nenhuma.
