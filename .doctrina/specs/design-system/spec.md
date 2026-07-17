# Spec — design-system

**Capability:** design-system
**Status:** active
**Implementation:** verified — as 3 slices landaram: fundação (0060), estados & feedback (0061) e orientação & navegação (0062).
**Realizes:** n/a — capability transversal de UI/UX (a gramática visual que todas as telas compartilham); não realiza um success-criteria específico do intake, habilita todos
**Last updated:** 2026-07-16
**Version:** 0.4.0

## Purpose

A gramática visual única do Arbites: os tokens, os componentes canônicos
(botão primário/secundário, input, card, badge), a hierarquia de
importância, os estados de feedback (salvo/carregando/erro/vazio/dirty), a
orientação espacial e a navegação assistida. Hoje o CSS (`styles.css`) e os
componentes reutilizáveis (`Modal`, `Autocomplete`, `ReadView`) existem, mas
sem um contrato explícito — telas divergem sutilmente (botões com pesos
diferentes, inputs com presença visual variável, blocos ora formulário ora
painel). Esta capability fixa as regras para que todas as telas leiam como um
sistema só, elevando a percepção de qualidade sem reescrever features.

Escopo detalhado (cada slice é uma change):

- **Fundação (0060):** componentes canônicos + hierarquia visual + CTA
  dominante.
- **Estados & feedback (0061):** salvo/carregando/erro/vazio/dirty + empty
  states úteis + ajuda contextual enxuta.
- **Orientação & navegação (0062):** breadcrumbs/header de contexto + busca
  global/comandos + layout de telas grandes.

## Requirements (EARS)

<!-- Requisitos de alto nível; o detalhe (por slice) chega nos deltas das
changes 0060/0061/0062 e é marcado [unverified] até implementar. -->

### Ubiquitous

- The system shall expor um conjunto fixo de componentes canônicos — botão
  primário (`button.primary`), botão secundário (`button` base), botão
  destrutivo (`button.danger`), input/select/textarea (seletor de elemento,
  altura `--h-control`), card (`.card` e as variantes `.metric-card`/
  `.chart-card`/`.todo-card` compartilhando UMA superfície) e badge de
  status (`status-dot` + `--dot`) — cada um com uma única aparência
  reutilizada em todas as telas.
- The system shall manter a superfície de card (fundo, borda, raio, padding,
  sombra) numa única definição CSS compartilhada pelas variantes, para não
  divergir tela a tela.
- The system shall estabelecer uma hierarquia visual explícita: título de
  página em `--fs-h1`/peso 700, subtítulo leve (`.subtitle`), espaço entre
  blocos por token (`.block` = `--s3`) em vez de margem mágica inline, e
  ausência de bordas duplicadas entre contêiner e conteúdo.
- The system shall sinalizar de forma consistente os estados de interação:
  **salvo** (toast transitório via `useToast`, em vez de save silencioso),
  **carregando** (`.spinner`/`.skeleton` canônicos), **falhou** (toast de
  erro + `.field-error` junto à ação, além do banner global), **vazio**
  (`.empty-state` com instrução) e **alterado-não-salvo/dirty** (o `Modal`
  compartilhado pede confirmação ao fechar via Esc/backdrop/X com o form
  sujo).
- The system shall oferecer navegação assistida além do menu lateral: uma
  paleta de comandos global (`CommandPalette`, Ctrl/Cmd+K de qualquer tela)
  que busca qualquer artefato via `GET /search` e navega até ele, mais
  ações rápidas (novo CT, nova execução, reindex); e orientação espacial
  (breadcrumbs nos back-bars das áreas profundas, largura de leitura
  limitada via `.content-narrow`).

### Unwanted-behavior (must-not)

- The system shall not apresentar múltiplas ações com o mesmo peso visual no
  mesmo bloco — no máximo uma ação de destaque (CTA dominante) por bloco.
- The system shall not exibir blocos de texto longos onde a interface já é
  autoexplicativa — a ajuda é curta e contextual.

## Acceptance criteria

<!-- Todos [unverified] enquanto planned; cada change (0060/0061/0062) landa
e prova a sua fatia, citando o teste/artefato. -->

1. [verified] Botão/​input/​card/​badge têm uma única definição reutilizada
   (uma classe/seletor canônico por tipo); a superfície de card é uma regra
   CSS compartilhada por `.card`/`.metric-card`/`.chart-card`/`.todo-card`
   (fim das divergências: `.chart-card` sem sombra e `.todo-card` com padding
   one-off); nenhum card de nível superior carrega mais `style={{
   marginBottom }}` ad-hoc — verified by `frontend/src/styles.css` (regra
   compartilhada + `.block`), varredura das telas e `npm run build` limpo.
2. [verified] Hierarquia aplicada: título de página em `--fs-h1`/700,
   `.subtitle` para apoio leve, ritmo de blocos via `.block` (`--s3`); no
   máximo um CTA `primary` por bloco nas telas (padrão já seguido, confirmado
   na varredura) — verified by `frontend/src/styles.css` + revisão das telas.
3. [verified] Os estados salvo/carregando/erro/vazio/dirty têm uma
   representação consistente e reutilizável: `Toast`/`useToast` (provider
   único no `main.tsx`), `.spinner`/`.skeleton`/`.field-error` no CSS, e a
   guarda de dirty no `Modal` compartilhado (confirma antes de descartar);
   toast de "salvo" ligado aos saves principais (decisões, defeitos,
   afazeres, reuniões, CT, requisitos) — verified by
   `frontend/src/components/Toast.tsx`, `frontend/src/components/Modal.tsx`
   (dirty), `frontend/src/styles.css` e build limpo. Rollout do toast às
   demais telas é incremental (skill `estados-de-feedback-nas-telas`).
4. [verified] Há uma busca global (Ctrl/Cmd+K) acessível de qualquer tela
   que encontra qualquer artefato via `GET /search` e navega até ele, com
   ações rápidas; as áreas profundas expõem contexto da rota (breadcrumbs
   nos back-bars) e a leitura tem largura limitada em telas grandes —
   verified by `frontend/src/components/CommandPalette.tsx`,
   `frontend/src/App.tsx` (listener Ctrl+K + breadcrumbs) e build limpo.

## Maturity

**MVP (committed):**

- Componentes canônicos, hierarquia, estados de feedback, orientação e
  navegação assistida — as três slices (0060/0061/0062).

**Future (aspirational, not committed):**

- Tokens de tema claro (hoje só o tema escuro está definido).
- Storybook / catálogo de componentes navegável.

## Out of scope for this spec

- A lógica de negócio de cada tela (métricas, execução, IA) — esta
  capability só governa a camada visual/UX compartilhada; o comportamento
  fica nas capabilities de feature (reporting, testcases, local-automation,
  ai-assist, …).
