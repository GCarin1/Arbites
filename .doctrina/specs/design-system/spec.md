# Spec — design-system

**Capability:** design-system
**Status:** draft
**Implementation:** planned — north-star escrito; detalhe e prova chegam pelas changes 0060 (fundação), 0061 (estados & feedback) e 0062 (orientação & navegação). Draft até a fundação (0060) landar.
**Realizes:** n/a — capability transversal de UI/UX (a gramática visual que todas as telas compartilham); não realiza um success-criteria específico do intake, habilita todos
**Last updated:** 2026-07-13
**Version:** 0.1.0

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
  primário, botão secundário, input, card e badge de status — cada um com
  uma única aparência (cor, altura, raio, padding, borda) reutilizada em
  todas as telas.
- The system shall estabelecer uma hierarquia visual explícita: títulos
  fortes, subtítulos leves, cards principais maiores que os secundários,
  espaço entre blocos e menos bordas repetidas.
- The system shall sinalizar de forma consistente os estados de interação —
  salvo, carregando, falhou, vazio e alterado-não-salvo (dirty).
- The system shall oferecer navegação assistida além do menu lateral (busca
  global / comandos rápidos) e orientação espacial (contexto da rota atual)
  nas áreas mais profundas.

### Unwanted-behavior (must-not)

- The system shall not apresentar múltiplas ações com o mesmo peso visual no
  mesmo bloco — no máximo uma ação de destaque (CTA dominante) por bloco.
- The system shall not exibir blocos de texto longos onde a interface já é
  autoexplicativa — a ajuda é curta e contextual.

## Acceptance criteria

<!-- Todos [unverified] enquanto planned; cada change (0060/0061/0062) landa
e prova a sua fatia, citando o teste/artefato. -->

1. [unverified] Botão/​input/​card/​badge têm uma única definição
   reutilizada (uma classe/componente canônico por tipo), sem variações
   ad-hoc por tela — landa em 0060.
2. [unverified] A hierarquia visual (título/subtítulo/card principal vs
   secundário/espaçamento) é aplicada de forma consistente — landa em 0060.
3. [unverified] Os estados salvo/carregando/erro/vazio/dirty têm uma
   representação consistente e reutilizável — landa em 0061.
4. [unverified] Áreas profundas expõem contexto da rota atual e há uma busca
   global/comando rápido acessível de qualquer tela — landa em 0062.

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
