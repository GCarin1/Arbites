# Arbites

Plataforma **local-first** de gestão e rastreabilidade de testes. Tudo que
existe na interface existe no disco: requisitos e casos de teste são
Markdown com frontmatter, o índice SQLite é descartável e reconstruível, e
os arquivos são editáveis no Obsidian sem conversão.

Cadeia de rastreabilidade: `Epic → Story → Test Case → Execution →
Evidência → Defeito`.

Roda no seu notebook sem nenhuma configuração. Para colocá-lo num servidor
do time — com login, contas e painel de administração —, veja
[docs/self-hosting.md](docs/self-hosting.md).

## Pré-requisitos

- Python 3.12+
- Node.js 18+ (apenas para buildar/desenvolver o frontend)

## Passo a passo para executar

### 1. Instalar dependências do backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Para rodar a suíte de testes, instale também as dependências de teste:

```powershell
pip install -r requirements-dev.txt
python -m pytest tests -q
```

### 2. Buildar o frontend (uma vez, ou após mudanças na UI)

```powershell
cd frontend
npm install
npm run build                  # gera frontend/dist, servido pelo backend
```

### 2.5. O `.env` (fora do Docker também)

O Arbites lê um arquivo `.env` **no diretório de onde você roda o comando**:

```
ARBITES_ADMIN_EMAIL=voce@exemplo.com
ARBITES_ADMIN_PASSWORD=uma-senha-longa-de-bootstrap
ARBITES_SIGNUP=off
ARBITES_GITHUB_TOKEN=github_pat_...      # opcional (ADR 0017)
```

Duas coisas que vale saber:

- **A variável de ambiente do processo ganha do arquivo.** Quem exportou na
  mão quis aquele valor agora; um `.env` esquecido no diretório não vence uma
  variável exportada.
- **Sem `ARBITES_ADMIN_EMAIL` e `ARBITES_ADMIN_PASSWORD`, nenhuma conta é
  criada** — e sem conta ninguém entra. O arranque diz isso em voz alta no
  log; antes ele falhava calado (change 0165). A senha precisa ter 12
  caracteres ou mais, e a conta nasce com troca obrigatória no primeiro login.

> Em Docker, quem lê o `.env` é o **Compose** — o arquivo já funcionava lá. O
> que a change 0165 corrigiu foi o caminho sem container, onde `python -m
> arbites serve` ignorava o arquivo e a instância subia sem admin.

### O `arbites.yaml`: o que é configurável

Ele nasce **comentado** na primeira execução, dentro do workspace, cobrindo
todos os blocos que o produto lê. Abrir o arquivo é a documentação.

**Segredo não entra nele** — ele fica dentro do workspace, que é versionável e
feito para ser compartilhado (ADR 0008). Chave de IA vai para o cofre do SO
(pela tela IA → Providers) e o token do GitHub vai para o cofre ou para o
`.env` (ADR 0017).

| bloco | para quê | default |
|---|---|---|
| `workspace.id_prefixes` | prefixo de ID por tipo (`CT`, `ST`, …) | os embutidos |
| `squads` | squads declarados, para os filtros sugerirem | vazio |
| `automation_targets` | projetos de automação; o sub-bloco `github` liga o disparo e a coleta | vazio |
| `risk_repos` | repositórios do mapa de risco | vazio |
| `ai` | provider, modelo e URL base — **nunca a chave** | nenhum |
| `observability` | de onde puxar CI, metas por sinal e retenção | nada vigiado |
| `audit.auto_interval_hours` | de quanto em quanto tempo uma rodada nova dispara | 24 |
| `requirements.vague_terms` | termos que o lint EARS marca como vagos | a lista embutida |
| `metric_thresholds` | semáforo do dashboard: `{warn, bad, direction}` | sem semáforo |
| `health_score.weights` | pesos da nota de saúde, renormalizados para 1.0 | 0.30 / 0.25 / 0.25 / 0.20 |
| `ci_monitoring.name_pattern` | como reconhecer execução de CI pelo nome | sem separação |

> Se o seu workspace é antigo, o arquivo dele continua como está — `ensure` só
> escreve quando não existe. Para ver o novo, crie um workspace vazio e copie
> os blocos que interessam.

> **Cuidado ao editar `automation_targets` à mão:** salvar os targets pela tela
> (Automação → Configurar) reescrevia o bloco inteiro e **apagava o sub-bloco
> `github:`** escrito à mão. Corrigido na change 0172: repositório, workflow
> e branch têm campos próprios na tela e sobrevivem ao salvamento. Um bloco
> pela metade (repositório sem workflow) não é gravado — ele só produziria um
> erro de disparo com o bloco aparentemente configurado no YAML.

### Não consigo entrar

O login responde **401 "e-mail ou senha inválidos"** para três situações
diferentes — conta inexistente, senha errada e conta não-ativa — e isso é
deliberado: distinguir "não existe" de "senha errada" entrega uma lista de
contas válidas a quem tenta adivinhar. De dentro da sua máquina, porém, você
tem direito à resposta:

```
python -m arbites admin
```

Ele diz quantas contas existem, com papel e status — ou avisa que **não existe
conta nenhuma**, que é o motivo mais comum do 401 numa instalação nova. Para
criar a primeira conta, ou redefinir a senha de uma que já existe:

```
python -m arbites admin --email voce@exemplo.com --password uma-senha-de-12-ou-mais
```

> **O caminho traiçoeiro:** se a conta já existe, o bootstrap por ambiente
> **nunca mais toca nela** — mudar `ARBITES_ADMIN_PASSWORD` no `.env` não muda
> a senha de uma conta criada antes. É para isso que serve o comando acima.

> **Me cadastrei pela tela e a conta ficou `viewer`/`pending`.** É o esperado:
> todo cadastro pelo formulário nasce pendente, aguardando um admin liberar.
> A armadilha é a instância que subiu **sem nenhum admin ativo** — aí não há
> quem aprove. Duas saídas, e a tela de login agora avisa qual delas serve:
>
> - com `ARBITES_ADMIN_EMAIL` declarado, **cadastre-se com exatamente esse
>   e-mail**: enquanto não existir admin ativo, essa conta nasce
>   `admin`/`active` com a senha que você escolher no cadastro. Assim que
>   existe um admin ativo, esse mesmo e-mail volta a nascer pendente;
> - sem nada declarado, use o `python -m arbites admin --email ... --password
>   ...` acima, que promove a conta que já existe e destrava o login junto.

### Trocar a senha

No **Perfil** (menu do avatar, canto superior direito) há o cartão **Senha**:
senha atual, nova e confirmação. Trocar derruba as **outras** sessões da
conta — a que você está usando continua aberta. Mínimo de 12 caracteres.

Quando a conta nasce pelo `python -m arbites admin` ou pelo bootstrap por
ambiente, ela vem com **troca obrigatória**: a senha passou pelo histórico do
shell ou pelo `docker inspect`, então serve para entrar uma vez. Nesse caso o
login abre direto a tela "Definir uma senha", e até a troca acontecer o
backend recusa todas as outras rotas com `password_change_required` — a SPA
devolve você à tela de troca em vez de ficar pedindo dados que não virão.

**Trancado fora por tentativas?** Cinco falhas em 15 minutos bloqueiam a conta
e o IP. Você pode esperar os 15 minutos contados a partir da última tentativa,
ou destravar na hora:

```
python -m arbites unlock                      # todas as contas
python -m arbites unlock --email voce@exemplo.com
```

(Redefinir a senha pelo `admin` já destrava a conta junto — quem chegou lá
provavelmente errou a senha algumas vezes.)

### 3. Subir a plataforma (um comando sobe tudo)

```powershell
cd backend
python -m arbites serve
```

Abra **http://localhost:8347**. A API fica em
`http://localhost:8347/api/v1` e a UI é servida na raiz.

O workspace default é `backend/workspace/` (criado automaticamente na
primeira execução, com `arbites.yaml` default). Para apontar para outro
diretório:

```powershell
python -m arbites serve --workspace D:\qa\meu-workspace
# ou via variável de ambiente:
$env:ARBITES_WORKSPACE = "D:\qa\meu-workspace"; python -m arbites serve
```

### 4. (Opcional) Modo desenvolvimento do frontend

Com o backend rodando em 8347, em outro terminal:

```powershell
cd frontend
npm run dev                    # Vite em http://localhost:5173, proxy /api → 8347
```

## Comandos úteis

```powershell
python -m arbites reindex                  # reconstrói o índice do zero
python -m pytest backend/tests -q         # testes do backend (na raiz do repo)
npm --prefix frontend run build            # build + typecheck do frontend
```

- O índice (`workspace/.arbites/index.db`) é **descartável**: pode apagar
  a qualquer momento; `reindex` (ou a subida do servidor) reconstrói tudo
  a partir dos arquivos.
- Edições feitas fora da UI (Obsidian, VS Code, Notepad) aparecem na
  interface em segundos — o watcher reindexa o arquivo alterado.
- Excluir pela UI/API nunca apaga: o arquivo vai para
  `workspace/.arbites/trash/`.
- Se o workspace for versionado em git, recomenda-se colocar `.arbites/`
  no `.gitignore` do workspace.

## Servidor MCP: o agente alcança o workspace

O Arbites publica um servidor **MCP** local, para um agente (Cursor, Claude
Desktop, qualquer cliente MCP) consultar o workspace. Ele não é um segundo
backend: fala HTTP com a instância, autenticado por uma credencial de agente,
e passa pelo mesmo gate de papel, módulo desligado e log de atividade que o
navegador.

**1. Gere a credencial** (ela é separada da sessão do navegador — revogar uma
não derruba a outra, e ela herda o papel da sua conta):

```
POST /api/v1/profile/agent-tokens   {"name": "cursor"}
```

O token em claro aparece **uma vez**. Guarde-o.

**2. Aponte o cliente MCP** para o servidor:

```json
{
  "mcpServers": {
    "arbites": {
      "command": "python",
      "args": ["-m", "arbites.mcp"],
      "env": {
        "ARBITES_URL": "http://192.168.0.17:8347",
        "ARBITES_TOKEN": "arb_..."
      }
    }
  }
}
```

**O que o agente ganha.** Só respostas que ele não calcula sozinho lendo o
repositório — um espelho da REST não agregaria nada:

| ferramenta | responde |
|---|---|
| `coverage_gaps` | o que falta cobrir, por story e **por critério EARS** — a lista, não só a contagem |
| `impact_of_files` | quais casos um diff afeta: `by_tag` (vínculo, fato) separado de `by_risk` (correlação, palpite) |
| `pending_rerun` | casos cujos passos mudaram depois do último resultado |
| `context_pack` | o pacote de contexto de um escopo (exige epic, story ou squad) |
| `execution_report` | resultado, passos e evidências de um ciclo |
| `external_links` | o que já está ligado a um sistema externo — a consulta que evita criar duplicata |
| `integration_capabilities` | o que cada sistema externo consegue representar, e o que ele **não** guarda |

**As três escritas** (change 0147), disponíveis só com `mcp_write` ligado:

| ferramenta | faz |
|---|---|
| `create_or_update_testcase` | grava o caso em BDD. **Idempotente pelo vínculo**: com o mesmo `system` + `remote_id`, a segunda chamada atualiza o caso existente em vez de criar outro |
| `record_result` | resultado de um caso num ciclo **aberto**, com passos e evidência em base64 |
| `link_external` | registra que CT-0007 ↔ CARD-4821 no sistema X |

Cada uma tem uma gêmea `*_preview` que **calcula e não grava**: o agente a
chama primeiro, mostra o plano (`action` diz `create` ou `update`, `changes`
diz o que muda) e só grava depois da sua confirmação. As duas são caminhos
diferentes na API de propósito — assim o log de atividade distingue quem
olhou de quem gravou.

`link_external` parece a menor das três e é a mais importante: sem ela o
agente não tem como saber, numa conversa nova, que já criou aquele card — e
recria. Com ela o fluxo vira *"o que daqui ainda não está lá?"* → resposta
determinística → age só no delta.

Três recusas que valem conhecer:

- **meio vínculo** (`system` sem `remote_id`, ou o contrário) é recusado: não
  é idempotente, e é assim que a duplicata nasce;
- **conflito** — o artefato mudou dos dois lados desde a última sincronia —
  é recusado nomeando o conflito. Escolher um lado aqui apagaria o outro em
  silêncio. A detecção depende do agente informar `revision` (a revisão atual
  do lado de lá): o Arbites não fala com o sistema externo, então sem isso ele
  só consegue responder *"mudou aqui?"*, e não finge saber mais;
- **`remote_id` já usado** por outro artefato daqui: dois casos apontando
  para o mesmo card tornam a próxima sincronia indecidível.

Evidência vai em **base64**, nunca como caminho no disco: um caminho vindo do
agente seria uma primitiva de leitura de arquivo arbitrário na máquina de
quem hospeda.

Casos também são expostos como recurso (`arbites://testcase/CT-0007`), para
o agente referenciar sem recolar o corpo na conversa.

Um resultado com a chave `refused` significa que o servidor recusou — em
geral porque o administrador desligou aquele módulo em Administração →
Sistema. O motivo vem junto.

**Os dois interruptores do MCP** ficam na própria página (IA → MCP) e em
Administração → Sistema:

| interruptor | padrão | o que faz quando desligado |
|---|---|---|
| `mcp_server` | **ligado** | nenhuma credencial de agente funciona; a sua sessão no navegador não é afetada |
| `mcp_write` | **desligado** | o agente lê mas não altera nada — qualquer método de escrita vindo dele é recusado com `agent_write_disabled` |

`mcp_write` nasce desligado de propósito: quase todo interruptor do Arbites
nasce ligado para preservar o comportamento de quem já instalou, mas o que
**concede poder novo** segue o contrário — quem quer conceder liga de
propósito.

**Gerenciar credenciais:**

```
GET    /api/v1/profile/agent-tokens         # lista (nome, criada, último uso)
POST   /api/v1/profile/agent-tokens         # {"name": "cursor"} → token em claro, uma vez
DELETE /api/v1/profile/agent-tokens/{id}    # revoga
```

Revogar a credencial do agente **não** derruba a sua sessão no navegador, e
sair do navegador não derruba o agente — são credenciais diferentes, de
propósito.

## Vínculo com o sistema oficial

Um caso de teste ou requisito pode guardar a que ele corresponde num sistema
externo. O vínculo mora no **frontmatter do próprio arquivo**, não só no
índice — o índice é descartável, e um reindex não pode apagar a memória do
que já foi sincronizado:

```yaml
external:
  - system: businessmap
    id: "CARD-4821"
    revision: "17"           # o que o remoto tinha na última sincronia
    synced_hash: "a3f01e…"   # o que NÓS tínhamos naquele momento
    synced_at: "2026-09-14T19:40:00Z"
```

Mais de um sistema por artefato é suportado de propósito: numa migração
corporativa os dois convivem, e perder o vínculo antigo enquanto o novo
nasce é perder o rastro quando ele mais importa.

`synced_hash` é o que permite responder **"mudou?"** — data só responde
"quando". Com ele o Arbites classifica cada vínculo em `never_synced`,
`in_sync`, `local_changed`, `remote_changed` ou `conflict`.

```
GET    /api/v1/integrations/links?system=&state=      # o que está ligado, e em que estado
PUT    /api/v1/integrations/links/{kind}/{id}         # registra/atualiza o vínculo de UM sistema
DELETE /api/v1/integrations/links/{kind}/{id}/{sys}   # desliga de um sistema
GET    /api/v1/integrations/capabilities              # o que cada sistema consegue representar
```

**Conflito nunca é resolvido sozinho.** Quando os dois lados mudaram desde a
última sincronia, nenhum é sobrescrito — último-que-escreve-vence é perda
silenciosa de dado, e numa ferramenta de rastreabilidade é o pior defeito
possível.

## Observabilidade: trazer para cá o que roda no GitHub

O Arbites puxa do GitHub Actions os runs que **ninguém disparou daqui** — o
`schedule` que roda de madrugada colhendo telemetria, log, acessibilidade e
print. Puxa, não recebe por webhook: uma instância local não é alcançável
pela internet, e puxar dá de graça a retomada (ficar dias desligado traz o
intervalo inteiro, não só o run mais recente).

**Pelo jeito mais curto:** a aba Observabilidade tem o bloco **Origens** —
repositório, workflow e artifact (os dois últimos opcionais: em branco valem
"todos"). Ele grava no `arbites.yaml` por você, e aparece justamente quando
ainda não há execução nenhuma, que é quando a pergunta "por que não achou
nada?" surge. Declarar exige papel `admin`; ver o que está declarado, não.

Pelo arquivo, se preferir editar à mão:

```yaml
observability:
  sources:
    - provider: github
      repo: org/app
      workflow: qa-nightly.yml   # opcional; sem isso, todos os workflows
      artifact: observabilidade  # opcional; sem isso, todos os artifacts
  max_runs_per_poll: 50
  # Meta e direção são SUAS, não do Arbites: ele não tem como saber que
  # `lcp_ms` maior é pior nem qual número é aceitável neste produto. Sem
  # declarar, a tela diz que o sinal "subiu" — nunca que "piorou".
  goals:
    lcp_ms: { direction: lower, goal: 2500 }
    violacoes_axe: { direction: lower, goal: 0 }
    success_rate: { goal: 95 }
  # Sinal e anexo têm valores de vida diferentes — veja abaixo.
  retention:
    signals_days: 730       # dois anos
    attachments_days: 90    # um trimestre
```

Depois:

```
GET  /api/v1/ci/sources           # o que está declarado
PUT  /api/v1/ci/sources           # declara (admin) — o que a aba usa
POST /api/v1/ci/ingest            # puxa o que ainda não está no disco
GET  /api/v1/ci/runs?limit=50     # runs ingeridos, com sinais e anexos
GET  /api/v1/ci/signals           # que sinais existem (descobertos, não fixos)
GET  /api/v1/ci/observability/export?format=pdf|csv|md&days=30   # o painel em arquivo
GET  /api/v1/ci/signals/{name}?since=&until=   # a série de um sinal no tempo
```

Cada run vira um **arquivo** em `workspace/ci/<ano>/<provider>-<run_id>.md`,
com os sinais no frontmatter e os anexos ao lado, hasheados. O índice SQLite
é descartável (ADR 0001): apagá-lo e reconstruir devolve meses de série.
Ingerir duas vezes o mesmo run não duplica — a marca d'água é o disco, não um
contador guardado à parte.

### O manifesto: o que o artifact declara

O `arbites.json` publicado junto do artifact é o contrato. Versão 2:

```json
{
  "version": 2,
  "labels": {
    "componente": "carteira-mfe",
    "ambiente": "hml",
    "stack": "front",
    "versao": "1.24.0"
  },
  "signals": [
    { "kind": "performance", "name": "lcp_ms", "value": 2410, "unit": "ms" },
    { "kind": "coverage", "name": "cobertura_pct", "value": 82, "unit": "%" }
  ],
  "attachments": [
    { "kind": "analysis",   "path": "analysis.md",  "title": "Análise do deploy" },
    { "kind": "cucumber",   "path": "result.json" },
    { "kind": "axe",        "path": "axe.json",     "title": "Varredura axe-core" },
    { "kind": "log",        "path": "suite.log" },
    { "kind": "screenshot", "path": "print-falha.png", "title": "Tela na falha" }
  ]
}
```

**`trigger` diz quem MANDOU rodar.** Três repositórios diferentes participam
do mesmo evento: onde o teste mora (`b3/e2e-web`), onde a aplicação mora
(`b3/app-trader-web`, que fez o deploy) e quem disparou o workflow. A pergunta
"qual **produto** está quebrando" é sobre o segundo — e um repositório de teste
que serve trader, ordens e app reunia os três numa taxa só. Declare:

```json
"trigger": { "repo": "b3/app-trader-web", "environment": "prd", "ref": "v1.24.0" }
```

A aba mostra os dois recortes lado a lado, e um gráfico de **erros por
repositório de origem** — volume de falha, não taxa: 90% em mil execuções são
cem falhas, e 50% em duas são uma. Quem já usa `labels` pode declarar
`repo_origem` em vez do bloco.

**`labels` é o que resolve micro-frontend.** O repositório onde o workflow
mora **não** é o que está sob teste: o mesmo repositório de testes valida
vários componentes, e vários repositórios de deploy chamam a mesma suíte. Sem
rótulo, a taxa de sucesso vira a média de coisas diferentes, que não é a saúde
de nada. A chave é livre — a topologia é sua, não do Arbites. Rótulos com um
único valor, ou com um valor por execução (`versao`), ficam fora do recorte:
um não divide e o outro é identificador.

**`kind: "axe"` é lido nativamente.** Publique o JSON cru do axe-core e o
Arbites extrai regra, gravidade, critério da WCAG (da tag `wcag143` → `1.4.3`),
nível (A/AA/AAA), quantos **elementos** violam e em que página. Aceita o
resultado de uma rota (objeto) e de várias (lista). Quem usa outra ferramenta
declara `findings` direto no manifesto, com a mesma forma. A versão 1 do
manifesto continua válida.

Log, print e análise em Markdown viram anexos hasheados ao lado do run e
aparecem na descida (gráfico → execução → job → arquivo).

### A aba Evidências

Print, log, varredura e a análise que o pipeline escreveu ficam guardados ao
lado de cada execução, hasheados. Em **Observabilidade → Evidências** eles
viram uma superfície do **período**, e não de um run só: até aqui, para ver o
print da falha era preciso já saber em qual execução ela aconteceu — o que
inverte a ordem natural, porque muitas vezes é o print que diz onde olhar.

Cada peça carrega o contexto da execução que a produziu (o repositório de
origem, o resultado, a data) — sem isso um print solto não é evidência de
nada. Clique na peça para abrir o arquivo; clique na execução para descer até
ela. Os filtros são tipo, repositório de origem e **só das execuções que
falharam**, que vem ligado: o print de um run verde quase nunca é o que se
procura.

### A aba Análise: o agente que junta tudo

O painel responde perguntas isoladas — "está piorando?", "qual produto
quebra?", "onde estão as violações?". Ninguém junta as três no fim do dia.

Em **Observabilidade → Análise**, o agente lê o período inteiro (saúde, sinais
com meta e direção declaradas, cenários instáveis, acessibilidade com WCAG e os
dois recortes de repositório) e escreve o veredito: síntese, saúde em uma
palavra, riscos com o número que os sustenta, e o que fazer — cada ação com o
alvo, que costuma ser um repositório de origem.

A análise vira **arquivo** em `workspace/ci/analises/ANL-AAAAMMDD-N.md`, com o
**dossiê no frontmatter** e o veredito no corpo. Guardar os números junto do
texto é o que permite comparar depois: comparar só o texto seria resenha de
resenha, e no dia em que a retenção apagar os runs antigos nem o texto teria
com o que ser conferido. Sendo arquivo, o histórico sobrevive a um reindex
(ADR 0001).

**Comparar duas análises** entrega os dois dossiês e os dois vereditos ao
modelo e pede o julgamento — que é o que um humano faria com as duas folhas
lado a lado. "Melhorou" não se calcula no código: `success_rate` subiu e
`lcp_ms` também não diz se o produto está melhor. A comparação vai sempre da
mais antiga para a mais recente, e separa **melhorou**, **piorou** e
**continua igual** — o que ficou parado costuma ser o que ninguém pegou.

Exige um provider de IA configurado em **IA → Providers**; sem ele a
plataforma segue inteira, só sem esta aba.

### Exportar o painel

No cabeçalho da aba, ao lado do período, há **PDF**, **CSV** e **MD**. São três
perguntas diferentes, não três botões para a mesma:

- **PDF** — o painel *com os gráficos*, para anexar num e-mail ou levar para
  uma reunião. A série é desenhada dentro do arquivo, não capturada da tela:
  exportar não depende de haver um navegador aberto.
- **CSV** — uma linha por **medida** (sinal, quando, valor, meta, execução de
  origem, conclusão, URL). É o formato que a planilha filtra e agrupa sem
  ninguém desempilhar nada antes, para cruzar com o que o Arbites não conhece.
- **MD** — o painel em texto, para ata, issue e wiki; continua legível daqui a
  um ano sem leitor especial.
- **CSV de acessibilidade** (botão na aba Acessibilidade) — as regras violadas
  com gravidade, critério WCAG e número de elementos, para priorizar fora daqui.

O PDF leva as **pizzas**, a saúde **por repositório** e a seção de
**acessibilidade** com os critérios da WCAG, além das séries.

O arquivo sai nomeado pelo fim do período (`observabilidade-2026-09-16.pdf`) e
respeita o período escolhido no seletor.

### A aba Observabilidade

Fica ao lado do Dashboard, e não dentro dele: a diferença não é o nome, é o
**eixo**. O Dashboard responde *"como está agora"* — retrato, para quem
pergunta o estado. A Observabilidade responde *"o que mudou, quando e por
quê"*, e por isso toda resposta vem com o período anterior ao lado.

Quatro blocos, cada um nomeando a pergunta que responde:

- **O que mudou** — o que se moveu sozinho: quebra depois de uma sequência
  verde, sinal que regrediu, teste que **virou** instável, e o silêncio da
  ingestão (período sem run **é dito**, porque num gráfico ausência de dado se
  parece com boa notícia).
- **Testes instáveis** — cenários que passaram *e* falharam no período. Só os
  marcados como **novos** entram em "O que mudou": "está instável" não é
  notícia para quem já sabe; "virou" é. Falhar sempre também não entra — isso
  é defeito, e chamá-lo de instável faria alguém re-executar em vez de
  corrigir.
- **Saúde** — execuções e taxa de sucesso, sempre contra o período anterior e
  contra a meta declarada.
- **Sinais no tempo** — uma série por medida. **Cada ponto é clicável**: leva
  à execução que o produziu.
- **Execuções recentes** — por onde se começa a olhar.

Clicar num ponto abre a descida no lugar, sem trocar de aba: execução → jobs →
medidas → anexos (print, log) → a análise em Markdown renderizada.

### O manifesto: seu pipeline declara o que produziu

Coloque um `arbites.json` na raiz do artifact. É ele que faz um sinal **novo**
entrar sem mudança de código no Arbites:

```json
{
  "version": 1,
  "signals": [
    {"kind": "perf",  "name": "lcp_ms",         "value": 2431, "unit": "ms"},
    {"kind": "a11y",  "name": "violacoes_axe",  "value": 7,    "unit": "count"},
    {"kind": "test",  "name": "cenarios_falhos","value": 2,    "unit": "count"}
  ],
  "attachments": [
    {"kind": "analysis",   "path": "analysis.md", "title": "Análise da IA"},
    {"kind": "screenshot", "path": "shots/home.png"},
    {"kind": "log",        "path": "run.log"},
    {"kind": "cucumber",   "path": "cucumber.json"}
  ]
}
```

- **Sinal** é `(kind, name, value, unit, at)` e nada mais. O Arbites não sabe
  que `lcp_ms` maior é pior — direção e meta são configuração de quem instala,
  não semântica embutida no código.
- **Anexo** é o que não é número: print, log e o `.md` da análise. O anexo de
  `kind: analysis` vira o **corpo** do documento do run — a análise que a sua
  automação já escreveu não é reescrita aqui.
- **`kind: cucumber`** é especial: além de virar anexo, o arquivo é lido
  **por cenário**, e é isso que permite apontar o teste que *virou instável*
  (a tag `@CT-XXXX` liga o cenário ao caso, ADR 0003). Sem ele o Arbites só
  enxerga a medida agregada, e "2 cenários falharam" não diz *qual* balança.
- **Sem manifesto** o Arbites reconhece anexo por convenção de nome
  (`*.log`, `*.png`, `analysis.md`, `cucumber.json`), **não extrai sinal
  nenhum** e marca o run com um aviso (`ingest_warning`). Convenção acerta
  hoje e quebra calada no dia em que alguém renomeia um arquivo — por isso ela
  avisa em vez de fingir que deu certo.

Emitir o manifesto no fim do seu workflow é uma linha:

```yaml
      - run: python gera_manifesto.py > arbites.json
      - uses: actions/upload-artifact@v4
        with:
          name: observabilidade
          path: |
            arbites.json
            analysis.md
            shots/
            run.log
```

### Retenção: o print some, a série fica

Um cron diário com prints enche disco — é aritmética, não hipótese. Por isso
a retenção é decidida junto com a ingestão, e **sinal e anexo têm janelas
independentes**:

- **Sinal** é barato (um número) e é o que faz a série: **730 dias** por padrão.
- **Anexo** (print, log, artifact) é caro e só interessa perto do evento:
  **90 dias** por padrão, e some primeiro.

O resultado é o trade-off certo: *"a acessibilidade regrediu em agosto?"*
continua respondida muito depois do print daquele dia ter ido embora.

O bloco **Espaço e retenção**, no fim da aba Observabilidade, mostra quanto
está ocupado e **o que a próxima limpeza levaria, antes de levar** — limpeza
que só conta o que fez depois de feita obriga a confiar sem poder conferir. O
removido vai para `.arbites/trash/` e volta enquanto a lixeira não for
esvaziada. Aplicar exige papel `admin`; ver a prévia, não.

```
GET  /api/v1/ci/retention          # ocupação + prévia do que sairia
POST /api/v1/ci/retention/apply    # executa exatamente a prévia, para a lixeira
```

Uma execução que passa até da janela do **sinal** sai inteira, anexos junto.

### A credencial vai falhar um dia — e isso não pode ser em silêncio

Não há data de descontinuação anunciada para o PAT classic; o GitHub apenas
recomenda o fine-grained. O risco real é outro: o fine-grained **expira em no
máximo 366 dias** e a organização pode **revogá-lo** a qualquer momento. Ou
seja, a credencial falha por desenho — e com a ingestão contínua ela pararia
sem ninguém notar, até alguém reparar que a observabilidade congelou.

Ao salvar o token em **Automação → Configurar** há um campo de **validade**
(opcional). Ela não é segredo — é uma data, e existe para o Arbites avisar
**antes**:

- faltando 14 dias ou menos, aparece em **Problemas** com o prazo;
- um `401`, ou um `403` que não é limite de taxa, vira um problema em
  **Problemas** com o motivo que o próprio GitHub deu (`Bad credentials` e
  `Resource not accessible by personal access token` pedem ações diferentes);
- a ingestão informa que parou **por credencial** — estado diferente de "não
  há execução nova", que na tela se parecem e pedem ações opostas.

Repor o token retoma do ponto em que parou: a marca d'água é o disco, então o
intervalo perdido volta inteiro.

> O token continua só no keyring do SO (ADR 0008) — nunca no YAML, nunca no
> índice, nunca logado. E um período sem run é visível na série em vez de
> passar por "semana tranquila".

**Em container não há cofre do SO** (ADR 0017). Lá a credencial entra pela
variável de ambiente `ARBITES_GITHUB_TOKEN`, já prevista no
`docker-compose.yml` — o mesmo canal por onde a senha de bootstrap do admin
chega. O ambiente tem precedência sobre o cofre quando os dois existem: quem
definiu a variável quis aquele token.

Sem cofre e sem a variável, a aplicação **sobe normalmente** — só a automação
de CI e a observabilidade ficam sem credencial, e a tela **Problemas** diz
isso com o remédio. Tentar salvar o token pela tela responde `409` explicando
a saída, em vez de falhar depois. O valor nunca volta em resposta nenhuma, e
nunca toca o disco do workspace.

## Afazeres e listas de To Do

Duas coisas diferentes na mesma página, em abas:

- **Afazer** é a nota adesiva: uma coisa a fazer, com prazo, status e **cor na
  borda inteira** — trocar o status muda a cor do cartão.
- **Lista de To Do** é o roteiro: passos que só fazem sentido juntos, com prazo
  **da lista**.

A linha da lista **não tem prazo próprio**, e é isso que dá sentido ao vínculo:
quando uma linha precisa de prazo, de status e de aparecer no sino, você a
vincula a um afazer. **O afazer traz a data; a linha traz o passo.**

O vínculo é **um-para-um** e é gravado só na linha — guardá-lo dos dois lados
abriria a chance de se contradizerem, e aí alguém teria de decidir qual está
certo sem ter como. A linha mostra o afazer resolvido (prazo e status, sem
trocar de tela) e o afazer mostra de que linha participa.

A lista é um arquivo em `workspace/todolists/`, com as linhas no frontmatter —
editável num editor de texto como todo o resto.

```
GET/POST  /api/v1/todolists                       # listar e criar
PUT/DELETE /api/v1/todolists/{id}                 # editar e mover para a lixeira
POST      /api/v1/todolists/{id}/items            # {"text": "...", "todo": "TD-0007"}
PUT/DELETE /api/v1/todolists/{id}/items/{item_id}
```

## O sino: o que mudou enquanto você não estava olhando

No canto superior direito, ao lado da busca. O número no ícone é quanto há de
não lido.

**A lista é o estado de AGORA, não uma caixa de entrada.** Ela é calculada das
fontes que já são verdade — os avisos do índice, a credencial, o painel de
observabilidade, os registros no disco. A consequência é deliberada: **um
problema resolvido some do sino mesmo sem ter sido lido**, porque deixou de
existir. Uma caixa de entrada gravada criaria um segundo estado, e o segundo
diverge do primeiro: o aviso corrigido ficaria na lista e quem clicasse não
acharia nada lá.

O que o Arbites guarda por pessoa é só **o que você leu** e **até onde
limpou**. Cada item tem um id estável, então "lido" gruda mesmo quando a lista
inteira é recalculada.

Quatro origens:

| origem | o que traz |
|---|---|
| **prazo** | afazer e lista que **vencem hoje** ou já venceram. Vencido é problema; vence hoje é atenção. O vencido volta a não-lido a cada dia: silenciar para sempre algo atrasado é o contrário do que um lembrete faz |
| **problema** | os avisos do índice e da credencial — a aba **Problemas** vira uma das fontes do sino, e continua existindo: o sino é ambiente, a aba é triagem |
| **observabilidade** | o que mudou sozinho: quebrou, virou instável, o silêncio da ingestão, sinal que regrediu |
| **concluído** | ação do **sistema** que deu certo: ingestão trouxe execuções, rodada de auditoria, ciclo fechado. São as que acontecem sem ninguém olhando — por isso "criei um CT agora" não entra |
| **log** | o log de atividade, **só admin** e só com o interruptor `notifications_info` ligado. Nasce desligado: é o único volume capaz de inundar a lista |

Clicar leva à **origem** — ao item, não à lista dele, quando o nome do arquivo
carrega um ID. Cada item tem *lida / não lida*, e há *marcar todas como lidas*
e *limpar*.

**Limpar é marca d'água, não exclusão.** Não há o que apagar: a lista é
derivada. Grava-se "vi tudo até aqui" — e o motivo que continua valendo volta a
aparecer quando voltar a acontecer.

## Intercâmbio por arquivo: o piso que funciona com qualquer ferramenta

Adaptador por API só existe onde há API **e permissão** — e permissão, numa
empresa, é pedido que demora. Arquivo existe sempre: toda ferramenta de teste
do mercado importa CSV. Sem credencial, sem MCP, sem pedir nada para a TI.

```
GET  /api/v1/integrations/file/testcases          # exporta casos em CSV
GET  /api/v1/integrations/file/results?execution= # exporta resultados em CSV
POST /api/v1/integrations/file/testcases/preview  # {"content": "<csv>"} → o plano
POST /api/v1/integrations/file/testcases          # importa
POST /api/v1/integrations/file/cucumber/preview   # {"content": "<json>"} → cenários e a que CT ligam
```

O formato é **neutro** — não é o CSV de nenhuma ferramenta específica, é o que
sobrevive à ida e à volta sem perder identidade:

```
external_id,id,title,type,priority,status,story,tags,folder,body
```

`external_id` é o que dá a **idempotência**: exportar e reimportar o mesmo
arquivo atualiza no lugar em vez de duplicar. Linha sem `external_id` é
importada, mas a prévia avisa que a volta vai duplicar — sem identidade
externa não há como reconhecer o que já entrou.

Três coisas que a prévia diz **antes**, e não depois:

- **evidência sai como caminho relativo, não como anexo.** Um CSV com print em
  base64 fica intratável em qualquer planilha;
- **linha sem `title`** falha nomeando o número da linha, e o cabeçalho é
  validado antes de qualquer linha — importar 40 de 50 e calar sobre as 10 é
  pior do que não importar, porque o buraco não aparece;
- **`external_id` repetido no mesmo arquivo** é ignorado e contado: duas
  linhas para o mesmo item tornam indecidível qual vale.

Para o Cucumber JSON, a ligação cenário ↔ caso é a tag `@CT-XXXX` (ADR 0003);
cenário sem tag aparece em `unmatched`, com aviso.

> Por enquanto essas rotas não têm tela: são API. O uso previsto é pela linha
> de comando ou pelo agente MCP, que alcança as mesmas rotas.

### Empurrar um ciclo inteiro de uma vez

O agente é a ponte certa para o fluxo com humano no meio e a ponte **errada**
para volume: empurrar 47 resultados não deveria custar 47 turnos de agente,
47 confirmações, nem variar de uma execução para outra.

```
GET  /api/v1/integrations/bulk/{exec_id}/preview?system=file   # o delta
POST /api/v1/integrations/bulk/{exec_id}?system=file           # empurra
```

Quatro mecânicas, cada uma contra um jeito específico de perder dado:

- **repetir não duplica** — a idempotência vem do vínculo, não da memória de
  quem chamou: o que já foi tem vínculo, e o que tem vínculo sai do delta;
- **marca item a item, no momento em que vai** — marcar só no fim deixaria,
  numa queda no meio, metade sincronizada sem registro, e a retomada
  reenviaria tudo;
- **conflito sai do lote, não trava o lote** — um artefato que precisa de uma
  pessoa não faz os outros 46 esperarem;
- **limite de taxa faz recuar, não descartar** — o item volta para a fila;
  perder item de lote é pior do que demorar.

> **O transporte que acompanha esta versão é só o de arquivo.** A orquestração
> (conjunto → delta → envio → marca → retomada) é genérica e roda sobre a
> porta, mas nenhum adaptador de API embarcado existe ainda: pedir `system=
> businessmap` é recusado com `no_transport` em vez de tentar e falhar mais
> tarde.

## Rodadas de auditoria: elas se acumulam sozinhas

A aba **Auditoria** dispara uma rodada nova sempre que a última passou de
`audit.auto_interval_hours` (24h por padrão) — inclusive só por alguém abrir
a aba. Cada rodada é um documento em `workspace/audits/`, então o histórico
cresce com o uso normal, sem ninguém pedir.

Para limpar, **com uma conta admin**, na aba Auditoria:

- **uma rodada** — menu `⋯` na linha do histórico → *Excluir rodada*;
- **em lote** — botão *Limpar antigas*, escolhendo uma data: leva tudo que é
  **anterior** a ela (a rodada da própria data fica).

Como todo o resto, a exclusão vai para `workspace/.arbites/trash/` e pode ser
restaurada. Pela API:

```
DELETE /api/v1/audit/{id}                     # uma rodada
DELETE /api/v1/audit?before=2026-08-01T00:00:00+00:00   # em lote
```

As duas exigem papel `admin`. Para aumentar o intervalo entre rodadas
automáticas — e com isso reduzir o acúmulo — ajuste
`audit.auto_interval_hours` no `arbites.yaml` do workspace.

> O **log de atividade** (aba Administração → Atividade) é outra coisa, com
> nome parecido: ele é contínuo e imutável de propósito, e não existe rota
> que o apague. Registro que o próprio suspeito apaga não prova nada.

## Conferir o layout em telefone

O Arbites é usado no celular — no corredor, na reunião, na fila. Medir se a
página estoura horizontalmente **não** prova que a tela está inteira: o que
quebra em 390px passa por baixo desse número. Texto some dentro de um cartão
que tem `overflow: hidden`, rótulo de coluna é escrito por cima do valor,
botão fica com alvo de 16px. A página não estoura em nenhum desses casos.

```
node frontend/scripts/audita-estreito.mjs \
  --url http://127.0.0.1:8000 --email voce@exemplo.com --senha ... --largura 390
```

Ele percorre as telas do menu (e as faixas internas da observabilidade)
medindo cinco famílias de quebra: `passa-da-viewport`,
`cortado-pelo-ancestral`, `texto-cortado`, `rotulo-sobre-o-valor` e
`alvo-pequeno` (WCAG 2.5.8 pede 24×24 CSS px). Sai com código 1 se achar
algo, então serve de gate. Rode também com `--largura 320`.

Playwright **não** é dependência do projeto — instalá-lo puxaria centenas de
MB para quem só quer rodar o Arbites. Aponte uma instalação existente com
`PLAYWRIGHT_ROOT=/caminho/para/node_modules`, ou
`npm i -D playwright && npx playwright install chromium`.

Tela nova? Acrescente-a à lista `TELAS` do script: uma tela que o detector
não visita é uma tela sem revisão.

## Estrutura do repositório

```
backend/    FastAPI + indexer SQLite + watcher (pacote arbites)
frontend/   React 18 + Vite + TypeScript (SPA, design dark GitHub-like)
.doctrina/  Specs EARS, ADRs e changes (framework Doctrina — fonte de verdade)
```

As specs em `.doctrina/specs/` são a verdade do comportamento; decisões de
arquitetura estão em `.doctrina/decisions/`.
