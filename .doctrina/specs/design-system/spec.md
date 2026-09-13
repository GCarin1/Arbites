# Spec — design-system

**Capability:** design-system
**Status:** active
**Implementation:** verified — as 3 slices landaram: fundação (0060), estados & feedback (0061) e orientação & navegação (0062).
**Realizes:** n/a — capability transversal de UI/UX (a gramática visual que todas as telas compartilham); não realiza um success-criteria específico do intake, habilita todos
**Last updated:** 2026-09-13
**Version:** 0.9.0

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
- The system shall usar `SingleRefInput` (busca por id E título via `GET
  /search`) em todo campo que referencia uma entidade existente
  (epic/story/CT/execution/defeito); `<datalist>` fica restrito a valores
  livres que não são entidades (ex.: squad) e `<select>` a conjuntos fixos
  de valores (status/prioridade/tipo). Nenhuma referência a entidade casa
  só por ID.
- The system shall refletir a aba ativa e os filtros de alto valor
  (squad do dashboard, filtro de status do repositório de CTs, período/ano
  da Memória, aba interna da Automação) num hash de URL restaurável
  (`#/<aba>?filtro=valor`), sem lib de router: `App.tsx` lê o hash no load,
  o escreve ao trocar aba/filtro e responde a `hashchange` (back/forward do
  navegador); o deep-link é compartilhável.
- The system shall apresentar a mesma interface em tela estreita com a barra lateral fora do fluxo, aberta por um controle no cabeçalho e fechada ao navegar, ao tocar fora e pelo Esc.
- The system shall reduzir o cabeçalho em tela estreita ao essencial — marca, busca e conta —, escondendo contadores do workspace, caminho do diretório e reindexar, que são controles de quem administra a instância.
- The system shall dar rolagem horizontal com encaixe por coluna ao Kanban em tela estreita, em vez de espremer as seis colunas na largura disponível.
- The system shall garantir alvo de toque de no mínimo 44 px de altura nos itens de navegação e nas ações de linha quando o ponteiro for grosseiro.
- The system shall oferecer degraus de espaçamento de 4px e 12px na escala de tokens, para que não haja valor de espaçamento decidido fora dela.
- The system shall oferecer três densidades de leitura — compacta, padrão e confortável — que alteram o respiro das linhas e a altura dos controles, preservando a separação entre seções.
- The system shall guardar a densidade escolhida no navegador de quem escolheu, por ser preferência de leitura de uma pessoa num aparelho, e não configuração do workspace.
- The system shall tornar cada card do quadro alcançável e operável por teclado — foco, abrir o resultado e mover entre colunas —, sem depender de arrastar.
- The system shall identificar cada card e cada coluna do quadro para tecnologia assistiva, dizendo de que caso se trata e em que coluna ele está.

### Event-driven

- When um caso muda de coluna, the system shall anunciar a mudança numa região viva, para que quem usa leitor de tela saiba o que aconteceu em vez de perceber o card sumir.

### State-driven

- While a gaveta de navegação está aberta, the system shall impedir a rolagem do conteúdo atrás dela e devolver o foco ao controle que a abriu quando ela fechar.

### Unwanted-behavior (must-not)

- The system shall not apresentar múltiplas ações com o mesmo peso visual no
  mesmo bloco — no máximo uma ação de destaque (CTA dominante) por bloco.
- The system shall not exibir blocos de texto longos onde a interface já é
  autoexplicativa — a ajuda é curta e contextual.
- The system shall not servir uma interface reduzida em funcionalidade na tela estreita; o que muda é a forma, e nenhuma tela deixa de ser alcançável.
- The system shall not deixar a densidade compacta reduzir um alvo interativo abaixo do mínimo de toque quando o ponteiro for grosseiro.
- The system shall not oferecer no quadro nenhuma ação que exista apenas como arrastar; arrastar com precisão é o gesto que exclui quem tem limitação motora.

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
5. [verified] Campos de referência a entidade usam `SingleRefInput`
   (id + título) em todas as telas — o Context Pack (epic/story) e o picker
   de CT da revisão por IA deixaram de usar `<datalist>`/`<select>` por ID;
   squad segue em `<datalist>` (valor livre) — verified by
   `frontend/src/components/AiAssist.tsx`, grep sem datalist-por-entidade e
   `npm run build` limpo.
6. [verified] Abrir uma URL com hash restaura a aba e os filtros
   serializados (dashboard squad, status do repositório, ano da Memória,
   aba da Automação); trocar aba/filtro atualiza o hash e back/forward do
   navegador navegam — verified by `frontend/src/App.tsx` (parse/serialize +
   listener `hashchange`), os filtros controlados nos componentes e
   `npm run build` limpo.
7. [verified] A casca declara o ponto de quebra, a gaveta e o cabeçalho enxuto, e nenhuma tela fica inalcançável em largura de celular — verified by `frontend/src/App.tsx` + `frontend/src/styles.css`.
8. [verified] Nenhuma tela em largura de 390 px transborda horizontalmente, e o que é largo por natureza rola dentro do próprio bloco — verified by `frontend/src/styles.css`.
9. [verified] As três densidades mudam quantas linhas cabem na mesma altura de tela, e a compacta não reduz nenhum alvo de toque abaixo do mínimo — verified by `frontend/src/styles.css` + `frontend/src/components/Profile.tsx`.
10. [verified] A escala de espaçamento cobre os degraus usados pela interface, e a densidade escolhida sobrevive ao recarregamento da página — verified by `frontend/src/styles.css` + `frontend/src/components/Profile.tsx`.
11. [verified] Um card do quadro recebe foco pelo teclado, abre o resultado por Enter e muda de coluna por atalho, com o mesmo efeito de arrastá-lo — verified by `frontend/src/components/Executions.tsx`.
12. [verified] Card e coluna se identificam para tecnologia assistiva e a mudança de coluna é anunciada numa região viva — verified by `frontend/src/components/Executions.tsx`.

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
