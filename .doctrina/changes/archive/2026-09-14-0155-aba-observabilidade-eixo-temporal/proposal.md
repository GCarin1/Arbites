# Change 0155-aba-observabilidade-eixo-temporal — aba de observabilidade com eixo temporal e descida do agregado ate o print, separada do dashboard que e retrato para gestor

- **Status:** applied
- **Applied:** 2026-09-14
- **Date:** 2026-09-14
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** reporting

## Why

aba de observabilidade com eixo temporal e descida do agregado ate o print, separada do dashboard que e retrato para gestor

## What

Uma aba **Observabilidade**, separada do Dashboard.

A diferença não é o nome, é **o eixo**. O Dashboard responde *"como está
agora"* — é retrato, e o público é quem pergunta o estado. Observabilidade
responde *"o que mudou, quando, e por quê"*. Fundir as duas produz uma tela
que não serve bem a ninguém (ADR 0016).

O padrão que Grafana, Datadog CI Visibility e Allure têm em comum, e que eu
seguiria:

1. **Tempo como eixo primário**, sempre com comparação ao período anterior.
2. **Descida obrigatória**: pico no gráfico → run → job → teste → print/log.
   Sem isso é decoração.
3. **Saúde declarada, não inferida**: não "87%", mas "87% contra a meta de
   95%, caindo há 3 dias".
4. **O que mudou sozinho**: teste que virou instável, tempo que dobrou,
   acessibilidade que regrediu.

**Toda visão responde uma pergunta acionável.** Bloco que não responde "o que
quebrou desde ontem", "que teste virou instável" ou "a acessibilidade
regrediu" não entra — observabilidade sem pergunta é mural de gráficos.

A análise de IA em `.md` da run é renderizada ali, ao lado dos sinais: ela é
a leitura que o pipeline já fez, e reescrevê-la seria desperdício.

## Scope boundaries

- Não remove nem esvazia o Dashboard: ele continua sendo o retrato para
  quem pergunta o estado.
- Não implementa alerta/notificação — ver é o primeiro passo; avisar é
  decisão seguinte.
- Não inventa sinal: só mostra o que a change 0154 ingeriu.

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
- [x] Cada bloco da tela nomeia, no próprio corpo, a pergunta que responde.
- [x] De um ponto no gráfico dá para chegar à run, ao job e ao print sem
      sair da aba.
- [x] Um período sem dado mostra estado vazio útil, não gráfico vazio.
- [x] Em 390 px a tela não rola de lado e os gráficos rolam dentro do bloco.

## Open questions

**"Teste que virou instável" ficou de fora, e de propósito.** O bloco "o que
mudou" entrega regressão de sinal, quebra depois de sequência verde, silêncio
da ingestão e run sem manifesto. Instabilidade é por CENÁRIO, e o manifesto
declara medida AGREGADA — a ingestão não recebe resultado por cenário. Somar
isso exige parsear o Cucumber JSON do artifact e ligá-lo aos CTs, o que é
ingestão nova e não um bloco de tela. Fica para change própria.
