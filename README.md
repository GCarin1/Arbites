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
