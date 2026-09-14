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

Declare as fontes no `arbites.yaml` do workspace:

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
POST /api/v1/ci/ingest            # puxa o que ainda não está no disco
GET  /api/v1/ci/runs?limit=50     # runs ingeridos, com sinais e anexos
GET  /api/v1/ci/signals           # que sinais existem (descobertos, não fixos)
GET  /api/v1/ci/signals/{name}?since=&until=   # a série de um sinal no tempo
```

Cada run vira um **arquivo** em `workspace/ci/<ano>/<provider>-<run_id>.md`,
com os sinais no frontmatter e os anexos ao lado, hasheados. O índice SQLite
é descartável (ADR 0001): apagá-lo e reconstruir devolve meses de série.
Ingerir duas vezes o mesmo run não duplica — a marca d'água é o disco, não um
contador guardado à parte.

### A aba Observabilidade

Fica ao lado do Dashboard, e não dentro dele: a diferença não é o nome, é o
**eixo**. O Dashboard responde *"como está agora"* — retrato, para quem
pergunta o estado. A Observabilidade responde *"o que mudou, quando e por
quê"*, e por isso toda resposta vem com o período anterior ao lado.

Quatro blocos, cada um nomeando a pergunta que responde:

- **O que mudou** — o que se moveu sozinho: quebra depois de uma sequência
  verde, sinal que regrediu, e o silêncio da ingestão (período sem run **é
  dito**, porque num gráfico ausência de dado se parece com boa notícia).
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
    {"kind": "log",        "path": "run.log"}
  ]
}
```

- **Sinal** é `(kind, name, value, unit, at)` e nada mais. O Arbites não sabe
  que `lcp_ms` maior é pior — direção e meta são configuração de quem instala,
  não semântica embutida no código.
- **Anexo** é o que não é número: print, log e o `.md` da análise. O anexo de
  `kind: analysis` vira o **corpo** do documento do run — a análise que a sua
  automação já escreveu não é reescrita aqui.
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

## Estrutura do repositório

```
backend/    FastAPI + indexer SQLite + watcher (pacote arbites)
frontend/   React 18 + Vite + TypeScript (SPA, design dark GitHub-like)
.doctrina/  Specs EARS, ADRs e changes (framework Doctrina — fonte de verdade)
```

As specs em `.doctrina/specs/` são a verdade do comportamento; decisões de
arquitetura estão em `.doctrina/decisions/`.
