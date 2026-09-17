# Spec — design-system

**Capability:** design-system
**Status:** active
**Implementation:** verified — as 3 slices landaram: fundação (0060), estados & feedback (0061) e orientação & navegação (0062).
**Realizes:** n/a — capability transversal de UI/UX (a gramática visual que todas as telas compartilham); não realiza um success-criteria específico do intake, habilita todos
**Last updated:** 2026-09-16
**Version:** 0.20.0

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
- The system shall derivar toda cor exibida — inclusive a de gráfico, grade, eixo e dica de valor — dos tokens em tempo de execução, admitindo valor escrito apenas como último recurso caso a leitura do token falhe.
- The system shall oferecer tema claro além do escuro, com a escolha guardada no navegador de quem escolheu e aplicada antes da primeira pintura.
- The system shall acompanhar cada item do menu lateral de um ícone, para que a navegação seja varrida e não lida item a item.
- The system shall agrupar o menu lateral apenas onde o grupo esclarece — sem cabeçalho para grupo de um item só — e ancorar no rodapé, separado por régua, o que é de manutenção e não de trabalho do dia.
- The system shall reservar a barra superior para identidade, busca e conta, mantendo informação de instalação e ação de manutenção acessíveis sem ocupar espaço permanente nela.
- The system shall posicionar as ações de uma tela dentro do cabeçalho dela, nunca antes do título da página.
- The system shall dimensionar cada campo de metadado pelo próprio conteúdo, sem esticá-lo até a altura do campo mais alto da mesma linha.
- The system shall separar a ação destrutiva da ação principal numa tela de detalhe, recolhendo-a num menu de ações em vez de deixá-la a um erro de mira.
- The system shall manter a ação destrutiva de uma linha de tabela num menu de ações, para que ela não compita com o conteúdo nem estique a altura da linha.
- The system shall impedir que identificador de artefato quebre em mais de uma linha em qualquer listagem.
- The system shall manter a caixa de marcar junto do seu rótulo, sem esticar o par pela largura disponível.
- The system shall dar rolagem horizontal a uma faixa de abas que nao cabe na largura disponivel, com sinal visivel do lado que ainda esconde aba e a aba ativa trazida ao campo de visao na troca, em vez de cortar a ultima aba na borda do quadro.
- The system shall impedir que os rotulos de uma linha de arvore se desenhem uns sobre os outros quando falta largura — so o elemento que recorta com reticencias cede espaco, e em tela estreita os metadados descem para uma segunda linha em vez de espremer o titulo.
- The system shall oferecer a escolha de arquivo pelo mesmo botao dos demais controles, com o nome do arquivo escolhido visivel e a possibilidade de reescolher o mesmo arquivo, sem expor o controle nativo do sistema operacional em nenhuma tela.
- The system shall manter o texto de um passo de execucao numa faixa propria em tela estreita, com as acoes e o status do passo na faixa seguinte, em vez de espremer o texto numa coluna ao lado dos botoes e deixar o status orfao numa terceira linha.
- The system shall montar todo estado vazio de lista de trabalho com marca visual, titulo da situacao, uma ou duas linhas dizendo o que mora ali, e a acao que resolve o vazio quando existe um proximo passo obvio, com a altura dada pelo conteudo.
- The system shall distinguir a lista que nunca teve item da lista cujo filtro nao alcancou nenhum, oferecendo criar no primeiro caso e limpar o filtro no segundo, para que ninguem crie um item que ja existe escondido pelo recorte.
- The system shall agrupar o menu por DONO do artefato e nao so por proximidade de fluxo — requisito e insumo do time de negocio e fica fora do grupo de trabalho de QA, antes dele, na ordem em que o fluxo acontece.
- The system shall manter, em tela de 320 a 390 px, todo texto dentro do seu contêiner, nenhum rótulo escrito por cima do valor que ele nomeia, e nenhum controle com alvo de toque abaixo de 24 CSS px — salvo exceção declarada no próprio elemento, com o caminho equivalente nomeado.
- The system shall empilhar as tabelas de dado em tela estreita, com cada linha virando cartão e cada célula carregando o rótulo da sua coluna, em vez de rolar de lado.

### Event-driven

- When um caso muda de coluna, the system shall anunciar a mudança numa região viva, para que quem usa leitor de tela saiba o que aconteceu em vez de perceber o card sumir.
- When uma requisição falha antes de obter resposta do servidor, the system shall informar que não foi possível falar com o servidor, em português e indicando o que verificar, em vez de repassar a mensagem interna do navegador.
- When uma exportação é pedida, the system shall mostrar progresso enquanto o arquivo é gerado e transferido, desabilitando os disparadores até terminar, e entregar o arquivo com o nome que o servidor sugeriu.

### State-driven

- While a gaveta de navegação está aberta, the system shall impedir a rolagem do conteúdo atrás dela e devolver o foco ao controle que a abriu quando ela fechar.
- While a pessoa não tiver escolhido um tema, the system shall seguir a preferência declarada pelo sistema operacional dela.
- While uma tela ainda não tem dado para mostrar, the system shall exibir o esqueleto do conteúdo que virá, em vez de uma frase solta.

### Unwanted-behavior (must-not)

- The system shall not apresentar múltiplas ações com o mesmo peso visual no
  mesmo bloco — no máximo uma ação de destaque (CTA dominante) por bloco.
- The system shall not exibir blocos de texto longos onde a interface já é
  autoexplicativa — a ajuda é curta e contextual.
- The system shall not servir uma interface reduzida em funcionalidade na tela estreita; o que muda é a forma, e nenhuma tela deixa de ser alcançável.
- The system shall not deixar a densidade compacta reduzir um alvo interativo abaixo do mínimo de toque quando o ponteiro for grosseiro.
- The system shall not oferecer no quadro nenhuma ação que exista apenas como arrastar; arrastar com precisão é o gesto que exclui quem tem limitação motora.
- The system shall not trocar o tema escuro por claro como padrão do produto; a escolha é de quem lê, e o escuro continua sendo o ponto de partida.
- The system shall not repetir no menu lateral a navegação que o menu da conta já oferece; o perfil é da pessoa e pertence ao avatar, o menu lateral é do workspace.
- The system shall not tratar o estouro horizontal da página como prova de layout responsivo; a verificação percorre as telas medindo texto cortado, rótulo sobreposto, corte pelo ancestral e alvo de toque.
- The system shall not exibir porcentagem de progresso quando o tamanho da resposta é desconhecido; uma barra que promete um número inexistente é pior que uma que só diz que está indo.

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
13. [verified] Grade, eixos, dica de valor e barras do gráfico acompanham o tema porque vêm dos tokens, e não de cor decidida no componente — verified by `frontend/src/components/Dashboard.tsx`.
14. [verified] O tema claro muda fundo, superfície, borda e texto mantendo os estados distinguíveis, e a escolha sobrevive ao recarregamento — verified by `frontend/src/styles.css` + `frontend/src/theme.ts`.
15. [verified] O menu lateral tem ícone em todo item, nenhum cabeçalho de grupo com um item só, e o que é de manutenção ancorado no rodapé depois de uma régua — verified by `frontend/src/App.tsx` + `frontend/src/styles.css`.
16. [verified] Nenhuma tela sai do alcance na reorganização: o que deixa o menu lateral continua acessível pelo menu da conta e pelo endereço direto — verified by `frontend/src/App.tsx`.
17. [verified] A barra superior não exibe caminho de disco nem ação de manutenção como botão de destaque, e ambos continuam alcançáveis — verified by `frontend/src/App.tsx`.
18. [verified] Nenhuma tela tem controle renderizado antes do título da página — verified by `frontend/src/App.tsx`.
19. [verified] Um campo de metadado vazio ocupa a altura de uma linha, e não a do campo mais alto ao lado dele — verified by `frontend/src/styles.css`.
20. [verified] A ação destrutiva de uma tela de detalhe fica num menu de ações, alcançável pelo teclado e fechando com Esc — verified by `frontend/src/components/OverflowMenu.tsx`.
21. [verified] A linha de uma tabela densa não é esticada pelas suas ações, e o identificador nela cabe numa linha só — verified by `frontend/src/styles.css` + `frontend/src/components/Defects.tsx`.
22. [verified] A caixa de marcar de um filtro fica ao lado do seu rótulo — verified by `frontend/src/styles.css`.
23. [verified] Uma falha de rede produz mensagem em português distinguindo "o servidor não respondeu" de uma recusa do servidor, em toda chamada — inclusive nos envios de arquivo — verified by `frontend/src/api.ts`.
24. [verified] Em 390 px a faixa de abas da tela de IA rola dentro de si — a caixa da aba "Configuracao" fica inteira apos rolar e a faixa exibe sombra no lado com aba escondida — e em 1440 px a mesma faixa nao rola nem exibe sombra — verified by `frontend/src/components/TabBar.tsx` + `frontend/src/styles.css`.
25. [unverified] Em 390 px nenhuma caixa de texto de uma linha das arvores de requisitos e de execucoes se sobrepoe a vizinha, o identificador aparece inteiro, e em 1440 px cada item continua numa linha so — verified by `frontend/src/styles.css`.
26. [unverified] Nenhuma tela exibe o controle de arquivo nativo — os quatro pontos de envio passam pelo botao do sistema, mostram o nome escolhido e aceitam reescolher o mesmo arquivo — verified by `frontend/src/components/FilePicker.tsx`.
27. [unverified] Em 390 px a linha de um passo de execucao cai em duas faixas (numero e texto; acoes e status) e em 1440 px continua numa faixa so — verified by `frontend/src/styles.css` + `frontend/src/components/Executions.tsx`.
28. [unverified] Num workspace novo as telas de test cases, requisitos, execucoes, defeitos e afazeres mostram estado vazio com marca, titulo, corpo e ao menos uma acao; com filtro que nao casa aparece o vazio de filtro, cuja acao e limpar — verified by `frontend/src/components/EmptyState.tsx` + `frontend/src/styles.css`.
29. [unverified] O menu apresenta Requisitos como item sem cabecalho de grupo, entre Hoje e o grupo Testes, que passa a conter apenas Test cases e Execucoes — verified by `frontend/src/App.tsx`.
30. [verified] As quinze telas do menu, incluindo as cinco faixas da observabilidade, não acusam nenhum achado a 390 px nem a 320 px no detector `frontend/scripts/audita-estreito.mjs`; e o detector, com a causa reintroduzida por CSS injetado, volta a acusar o rótulo sobreposto — verified by `frontend/scripts/audita-estreito.mjs`.
31. [verified] A exportação devolve tamanho e nome de arquivo em todos os formatos, inclusive num período sem dado — verified by `backend/tests/test_export_progresso.py`; e a barra em largura de telefone não estoura nem sobrepõe texto — verified by `frontend/scripts/audita-estreito.mjs`.

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
