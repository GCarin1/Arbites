---
name: gramatica-de-componentes-canonicos
description: Toda tela nova ou alterada usa exclusivamente os componentes canônicos (botão primário/secundário, input, card, badge) e a hierarquia visual do design-system — nunca estilos ad-hoc, nunca dois CTAs de mesmo peso no mesmo bloco.
when: O agente vai criar ou alterar qualquer componente/tela do frontend (novo card, formulário, botão, badge, seção de página).
---

# Skill — gramatica-de-componentes-canonicos

## When to use this skill

- O agente vai adicionar um botão, input, card ou badge em qualquer tela.
- O agente está criando uma tela/seção nova e precisa decidir tamanhos,
  espaçamentos e pesos visuais.
- O agente está revisando um diff de frontend que introduz classes CSS novas
  ou estilos inline.

## Procedure

1. **Nunca invente um estilo novo para um tipo que já tem canônico.** Antes
   de estilizar, grep no `styles.css` pela classe do tipo: botão
   (`.btn-primary`/`.btn-secondary` — enquanto 0060 não landa, `button` base
   + `button.primary`), input (altura `--h-control`), card (`.card`), badge
   (`status-dot` + rótulo texto, nunca cor sozinha).
2. **Um CTA de destaque por bloco, no máximo.** Se o bloco já tem uma ação
   primária, toda ação adicional entra como secundária (discreta). Se dois
   botões parecem igualmente importantes, um deles está errado — decida qual
   é o caminho principal do usuário.
3. **Hierarquia antes de borda.** Diferencie importância com tamanho/peso/
   espaço (`--fs-h*`, `--s3`/`--s4`), não com mais bordas. Card dentro de
   card com borda dupla é sinal de erro — o interno perde a borda.
4. **Use os tokens, não valores soltos.** Cores/espaços/raios/alturas vêm
   das variáveis CSS (`--primary`, `--s2`, `--r-card`, `--h-control`);
   um `padding: 13px` hardcoded quebra o ritmo do sistema.
5. **Status = ponto colorido + texto.** Nunca cor como único indicador
   (regra já existente na spec reporting, vale para toda a app).

## Anti-patterns

- Botões com estilos diferentes por tela ("call to action" numa tela,
  apagado na outra) — a inconsistência sutil derruba a percepção de
  qualidade mais que um defeito funcional.
- Vários botões de mesmo peso no mesmo bloco: se tudo grita, nada chama
  atenção.
- Bordas repetidas (contêiner com borda + filho com borda) para "separar"
  conteúdo que o espaçamento separaria melhor.
- `style={{ ... }}` inline para o que os tokens/classes canônicos já
  resolvem.

## Related material

- `.doctrina/specs/design-system/spec.md` — a capability que fixa esta
  gramática.
- `.doctrina/changes/0060-design-system-fundacao-gramatica-visual-unica/`
- `frontend/src/styles.css` — tokens (`:root`) e classes canônicas.
- [[leitura-agrupada-em-card]] · [[truncar-titulo-em-card]] — convenções de
  card já capturadas.
