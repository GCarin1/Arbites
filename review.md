Documento de Ajustes, Melhorias e Novas Features

1. Ajustes Gerais
1.1 Test Cases — Reestruturação Completa
Organização em Pastas (Repositório de Casos de Teste)
A estrutura de casos de teste deve funcionar como um repositório de arquivos hierárquico, permitindo organização livre por pastas. As regras são:

Estrutura hierárquica ilimitada — O usuário deve poder criar quantas pastas e subpastas desejar, sem limite de profundidade (pastas filhas de pastas filhas, recursivamente).

Centralização na tela — A árvore de pastas/casos de teste deve ser renderizada no centro da área de conteúdo, desvinculada do menu lateral. Conforme a quantidade de itens cresce, a estrutura deve permanecer legível e independente do sidebar, utilizando scroll próprio quando necessário.

Tela inicial do módulo — Ao abrir o projeto e navegar para "Test Cases", o usuário deve visualizar apenas a estrutura de repositório (árvore de pastas e casos de teste) centralizada na tela. Não deve haver tela vazia; a árvore é o conteúdo principal.

Navegação e Detalhe
Acesso ao detalhe — O detalhe de um caso de teste só deve ser aberto mediante clique explícito no item. Não deve haver preview lateral ou abertura automática.

Botão "Voltar" — Dentro da tela de detalhe de um caso de teste, deve existir um botão claro de "Voltar" que retorna o usuário à tela inicial do repositório (árvore de pastas).

Formato dos Casos de Teste
Todos os casos de teste devem seguir obrigatoriamente o formato BDD (Behavior-Driven Development), com a estrutura:


# [exemplo_formato_bdd.feature]
Feature: [Nome da Feature]

  Scenario: [Nome do Cenário]
    Given [pré-condição]
    When [ação executada]
    Then [resultado esperado]
Interações com a Árvore
Ação	Descrição
Drag & Drop	Arrastar casos de teste entre pastas
Expandir/Colapsar	Abrir e fechar pastas com clique
Excluir pasta	Remover pasta (com confirmação e tratamento de conteúdo interno)
Excluir caso de teste	Remover caso de teste individual (com confirmação)
Importação Inteligente via IA
Deve existir uma opção de importação em massa com as seguintes características:

Entrada aceita: Arquivos .txt, .md ou .xml contendo casos de teste em formato livre.

Processamento: O conteúdo do arquivo é enviado a uma IA que deve:

Interpretar e identificar cada caso de teste individualmente, mesmo que estejam em formatos não padronizados.
Criar automaticamente uma pasta (nomeada com base no contexto do arquivo).
Converter cada caso de teste identificado para o formato BDD da aplicação.
Adequar testes que estejam fora do padrão esperado, inferindo Given/When/Then a partir do contexto.
Requisito de performance: O processamento deve ser leve o suficiente para ser executado por modelos de IA com 9B de parâmetros ou menos (ex: modelos quantizados locais). O prompt e a lógica devem ser otimizados para baixo consumo de tokens.

Metadados Obrigatórios
Todo caso de teste deve registrar automaticamente a data de criação (timestamp), exibida na listagem e no detalhe.

1.2 Requisitos
O módulo de Requisitos deve replicar o mesmo layout e comportamento descrito para Test Cases:

Estrutura hierárquica de pastas ilimitada
Centralização na tela
Navegação com detalhe via clique e botão "Voltar"
Drag & Drop, expandir/colapsar, exclusão
Data de criação registrada
1.3 Execuções
O módulo de Execuções deve replicar o mesmo layout e comportamento descrito para Test Cases:

Estrutura hierárquica de pastas ilimitada
Centralização na tela
Navegação com detalhe via clique e botão "Voltar"
Drag & Drop, expandir/colapsar, exclusão
Data de criação registrada
1.4 Afazeres (To-Do)
Mudança de layout: Substituir o formato atual de tabela por um layout de cards/blocos, simulando um bloco de anotações visual. Cada afazer deve ser representado como um card individual, com aparência limpa e intuitiva — semelhante a sticky notes ou um quadro de tarefas pessoal.

1.5 Automação — Reformulação Completa
1.5.1 Execução Local
O módulo de automação para execução local deve oferecer o seguinte fluxo:

Etapa 1 — Seleção do diretório de features O usuário deve poder navegar e selecionar a pasta onde estão os arquivos .feature do projeto de automação.

Etapa 2 — Configuração e disparo do comando Interface para montar e executar o comando Behave:


# [comando_execucao_behave.sh]
behave <arquivo>.feature --tags=<tag_escolhida>
O usuário seleciona o arquivo .feature e a tag desejada via interface (dropdowns ou inputs com autocomplete).

Etapa 3 — Acompanhamento em tempo real Exibir um terminal/console embutido que mostra a execução do teste em tempo real (stdout/stderr).

Etapa 4 — Acesso a artefatos pós-execução Após a execução, o usuário deve poder acessar diretamente:

Artefato	Caminho
Logs	./logs/
Screenshots	./screenshots/
Análise de IA	./analise/
Etapa 5 — Configuração Local (.env) Deve existir uma seção de Configurações Locais que permite editar visualmente o arquivo .env do projeto. Cada variável de ambiente deve ser apresentada como um campo de input com:

Nome da variável (label)
Breve descrição do que deve ser preenchido
Input editável com o valor atual
As variáveis e suas descrições são:

Seção	Variável	Descrição
Credenciais de Teste	TEST_DOCUMENTO	Documento (CPF) utilizado para login nos testes
TEST_SENHA	Senha do usuário de teste
URLs	BASE_URL	URL base da aplicação sob teste
WebDriver Local	EDGE_DRIVER_PATH	Caminho personalizado para o msedgedriver (opcional)
HEADLESS	Executar sem interface gráfica (true/false)
WebDriver Manager	USE_WEBDRIVER_MANAGER	Se true, baixa o driver automaticamente via webdriver_manager
LOCAL_BROWSER	Navegador para execução local (edge, chrome)
Timeouts	PAGE_LOAD_TIMEOUT	Timeout de carregamento de página (segundos)
SCRIPT_TIMEOUT	Timeout de execução de scripts (segundos)
ELEMENT_WAIT_TIMEOUT	Timeout de espera por elementos (segundos)
BrowserStack — Ativação	USE_BROWSERSTACK	Ativar execução remota no BrowserStack (true/false)
BrowserStack — Credenciais	BROWSERSTACK_USERNAME	Username da conta BrowserStack
BROWSERSTACK_ACCESS_KEY	Access Key da conta BrowserStack
BrowserStack — Projeto	BROWSERSTACK_PROJECT_NAME	Nome do projeto no BrowserStack
BROWSERSTACK_BUILD_NAME	Nome da build/execução
BrowserStack — Browser	BROWSERSTACK_OS	Sistema operacional (Windows, OS X)
BROWSERSTACK_OS_VERSION	Versão do SO (11, 10, Ventura, etc.)
BROWSERSTACK_BROWSER	Navegador (Chrome, Firefox, Edge, Safari)
BROWSERSTACK_BROWSER_VERSION	Versão do navegador (latest, 120.0, etc.)
BrowserStack — Local Testing	BROWSERSTACK_LOCAL	Testar URLs internas/localhost (true/false)
Ambiente	ENVIRONMENT	Ambiente de execução (dev, staging, prod)
DEBUG	Habilitar logs de debug (true/false)
Logger	LOG_ENABLED	Habilitar/desabilitar logs (true/false)
LOG_LEVEL	Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_SAVE_TO_FILE	Salvar logs em arquivo (true/false)
LOG_SHOW_CONSOLE	Exibir logs no console (true/false)
LOG_MAX_FILE_SIZE	Tamanho máximo do arquivo de log em bytes
LOG_BACKUP_COUNT	Quantidade de arquivos de backup de log
Análise de Logs com IA	AI_LOG_ANALYZER_ENABLED	Habilitar análise de logs com IA (true/false)
OPENAI_API_KEY	Chave de API da OpenAI ou B3GPT
OPENAI_BASE_URL	URL base da API (vazio para OpenAI padrão)
OPENAI_API_VERSION	Versão da API (necessário para B3GPT/Azure)
OPENAI_MODEL	Modelo a ser utilizado (gpt-4o-mini, etc.)
OPENAI_MAX_TOKENS	Máximo de tokens na resposta
OPENAI_TEMPERATURE	Temperatura (0.0 = preciso, 1.0 = criativo)
AI_ANALYZE_ON_FAILURE_ONLY	Analisar apenas em falhas (true/false)
AI_SAVE_ANALYSIS_TO_FILE	Salvar análises em arquivo (true/false)
AI_MAX_LOG_LINES	Máximo de linhas do log enviadas para análise
1.5.2 Execução Remota via GitHub Actions
O projeto de automação já está hospedado em um repositório corporativo no GitHub (não pessoal) e possui um workflow configurado. A interface deve permitir disparar a execução remota informando os seguintes parâmetros:

Parâmetro	Descrição
Arquivo .feature	Qual feature será executada
Tag do Behave	Tag para filtrar cenários (@regressao, @smoke, etc.)
Ambiente	dev, cer ou prd
Navegador	chrome (padrão para CI)
Repositório de origem	Nome do repositório que disparou a execução
A interface deve permitir acompanhar o status da execução (pendente, em andamento, concluído, falhou) e acessar os artefatos gerados pelo workflow.

2. Nova Feature — Perfil do Usuário
2.1 Seção de Perfil
Criar uma nova seção de Perfil acessível pelo menu, contendo:

Informações pessoais — Campo editável para o nome do usuário e demais configurações futuras da ferramenta.

Memória de Longo Prazo para IA — Um bloco de texto em formato Markdown (.md) editável diretamente na interface, dividido em duas seções:

Seção	Propósito
Preferências & Estilo	Registra como o usuário prefere interagir com a IA (tom, formato de resposta, tecnologias utilizadas, etc.)
Contexto Ativo	Registra o contexto atual de trabalho do usuário (projetos em andamento, decisões recentes, informações relevantes)
Comportamento esperado:

Este conteúdo serve como contexto persistente que é injetado em qualquer interação com IA dentro da ferramenta, independentemente do modelo utilizado. A IA deve ser capaz de ler e editar esse contexto conforme o uso (adicionando novas informações relevantes ou atualizando contextos desatualizados), mantendo um histórico vivo e sempre atualizado do usuário.

3. Melhoria — Reestruturação do Menu Lateral (Sidebar)
3.1 Problema Atual
O menu lateral atual apresenta todos os módulos empilhados sem agrupamento lógico, tornando a navegação pouco intuitiva conforme a aplicação cresce.

3.2 Nova Estrutura Proposta
O menu lateral deve ser reorganizado em categorias semânticas com agrupamento visual claro:


📌 ACESSO RÁPIDO
    └── [Itens fixados pelo usuário via "pin"]

📐 PLANEJAMENTO
    ├── Requisitos
    ├── Test Cases
    └── Execuções

📊 ACOMPANHAMENTO
    ├── Dashboard
    ├── Daily
    └── Reuniões

🔧 FERRAMENTAS
    ├── Automação
    ├── IA
    └── Migração

🆘 SUPORTE
    └── Problemas
3.3 Funcionalidade de "Pin" (Acesso Rápido)
Cada item do menu deve possuir uma ação de fixar/pin (ícone de pin ao hover ou menu de contexto). Ao fixar um item, ele aparece duplicado na seção "Acesso Rápido" no topo do sidebar, permitindo navegação instantânea para os módulos mais utilizados pelo usuário. O usuário pode remover o pin a qualquer momento.

3.4 Comportamento Visual
As categorias devem ser colapsáveis (expandir/recolher) para que o usuário possa ocultar seções que não utiliza com frequência, mantendo o sidebar limpo.

Resumo de Prioridades
Prioridade	Item	Tipo
Alta	Reestruturação de Test Cases (pastas, centralização, BDD)	Ajuste
Alta	Reestruturação do Menu Lateral	Melhoria
Alta	Automação — Execução Local e Remota	Ajuste
Média	Perfil com Memória de Longo Prazo	Nova Feature
Média	Afazeres em formato de Cards	Ajuste
Média	Requisitos e Execuções (replicar layout de Test Cases)	Ajuste
Baixa	Importação inteligente via IA	Ajuste
Documento gerado em 2026-07-08. Sujeito a revisões conforme evolução do projeto.