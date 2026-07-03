# Arbites

Plataforma **local-first** de gestão e rastreabilidade de testes. Tudo que
existe na interface existe no disco: requisitos e casos de teste são
Markdown com frontmatter, o índice SQLite é descartável e reconstruível, e
os arquivos são editáveis no Obsidian sem conversão.

Cadeia de rastreabilidade: `Epic → Story → Test Case → Execution →
Evidência → Defeito`.

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

## Estrutura do repositório

```
backend/    FastAPI + indexer SQLite + watcher (pacote arbites)
frontend/   React 18 + Vite + TypeScript (SPA, design dark GitHub-like)
.doctrina/  Specs EARS, ADRs e changes (framework Doctrina — fonte de verdade)
```

As specs em `.doctrina/specs/` são a verdade do comportamento; decisões de
arquitetura estão em `.doctrina/decisions/`.
