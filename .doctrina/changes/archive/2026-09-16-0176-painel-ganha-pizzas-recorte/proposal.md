# Change 0176-painel-ganha-pizzas-recorte — painel ganha pizzas recorte por repositorio e componente aba de acessibilidade e configuracao em aba separada

- **Status:** applied
- **Applied:** 2026-09-16
- **Date:** 2026-09-16
- **Owner:** Gcarini
- **Lane:** runtime (uncertain; signals: configuracao) — opened anyway (--force)
- **Affects specs:** ci-automation

## Why

painel ganha pizzas recorte por repositorio e componente aba de acessibilidade e configuracao em aba separada

## What

- `frontend/src/components/Pizza.tsx` (novo): pizza em SVG com legenda que
  repete rótulo, valor e porcentagem — a cor nunca carrega o significado
  sozinha. Papéis fixos (verde/vermelho, a escala de gravidade do axe) e uma
  sequência neutra para o resto.
- `frontend/src/components/Observability.tsx`: três abas — **Painel**,
  **Acessibilidade**, **Configuração**. O painel ganhou as duas pizzas, a
  tabela por repositório e o recorte por rótulo; a acessibilidade virou aba
  própria com pizza por gravidade, regras mais violadas (com WCAG) e páginas;
  Origens e Retenção saíram do meio do painel e foram para Configuração.
- `backend/arbites/export_obs.py`: o PDF desenha as pizzas (setor por
  triângulos — o fpdf2 não tem arco preenchido), a saúde por repositório e a
  seção de acessibilidade; o Markdown ganhou as duas seções; e
  `format=findings` exporta as regras violadas em CSV.

## Scope boundaries

- A descida (gráfico → execução → job → anexo) não muda: prints e logs
  continuam sendo alcançados pelo run, não por uma galeria à parte.
- Sem gráfico de pizza para sinal numérico: sinal é série, e fatiar uma média
  no tempo não responde pergunta nenhuma.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [x] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [x] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [x] Verificado no navegador com 72 runs de 3 repositórios de micro-frontend
      e 1022 achados de acessibilidade: as três abas a 1440px e a 390px, sem
      estouro horizontal em nenhuma.
- [x] PDF do painel rico renderizado e conferido: pizzas, saúde por
      repositório e acessibilidade com WCAG.

## Open questions

Nenhuma.
