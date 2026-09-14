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
