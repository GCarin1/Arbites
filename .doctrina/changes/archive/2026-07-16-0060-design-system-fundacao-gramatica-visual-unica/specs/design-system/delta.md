# Spec Delta — capability: design-system

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/design-system/spec.md`

Note: 1ª das 3 slices. Landou → Implementation da capability de `planned`
para `partial`, Status draft → active, critérios #1/#2 → verified.

**Decisão de implementação (ajuste vs. a proposta):** a proposta original
sugeria criar `.btn-primary`/`.btn-secondary`. A auditoria do código mostrou
que a convenção canônica JÁ existe e é superior — `button` (base =
secundário) + `button.primary` + `button.danger`, via seletor de elemento,
usada consistentemente nas 16 telas. Introduzir `.btn-*` criaria DOIS
sistemas e churn em todo botão do repo sem ganho. Decidido: canonizar a
convenção existente (documentada na skill
`gramatica-de-componentes-canonicos`) em vez de renomear. Botão, input e
badge de status já eram canônicos; o trabalho real foi CONSOLIDAR a
superfície de card (que divergia) e a hierarquia/ritmo.

---

O que landou (detalha os requisitos de FUNDAÇÃO no spec):

### Ubiquitous

- Superfície de card unificada: UMA regra CSS compartilhada por
  `.card`/`.metric-card`/`.chart-card`/`.todo-card` (fundo/borda/raio/
  padding/sombra). Corrige as divergências reais achadas na auditoria:
  `.chart-card` não tinha sombra; `.todo-card` usava padding one-off
  `12px 14px` em vez de `--s2`.
- Ritmo de blocos por token: `.block` (`margin-bottom: --s3`) substitui o
  `style={{ marginBottom: 24 }}` ad-hoc (12 sites convertidos em
  AiAssist/Automation/Profile/Dashboard/ActivityHeatmap).
- Hierarquia: título de página em `--fs-h1`/peso 700 (antes usava `--fs-h2`,
  mais fraco que o próprio token h1 disponível); `.subtitle` para apoio leve.

### Unwanted-behavior (must-not)

- Card não repete a superfície por variante (uma definição só); card de
  nível superior não carrega margem mágica inline.

### Acceptance criteria

1. [verified] — ver spec (superfície compartilhada + `.block`, build limpo).
2. [verified] — ver spec (hierarquia + 1 CTA por bloco confirmado).
