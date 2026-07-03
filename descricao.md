# Arbites — Plataforma Local de Gestão e Rastreabilidade de Testes

> Documento de especificação v1.0 — 2026-07-02
> Substitui o projeto Probatio. Metodologia de construção: Doctrina (specs EARS onde aplicável, ADRs para decisões).

---

## 1. Visão

Plataforma de gestão de testes **local-first**, executada na máquina do usuário, cujo diferencial central é a **cadeia de rastreabilidade completa**:

```
Epic → Story → Test Case → Execution → Evidência → Defeito
```

O objetivo primário não é substituir Xray/Zephyr feature a feature. É responder, com prova, as perguntas que a chefia faz:

- "Essa história foi validada?"
- "Qual execução encontrou a falha?"
- "Quais evidências comprovam a aprovação?"
- "Qual a cobertura e o pass rate da sprint?"

Tudo que existe na interface existe no disco. A interface é uma visualização da estrutura real de arquivos.

### 1.1 Contexto do usuário

Fluxo atual na empresa: Miro (planejamento) → Confluence (detalhe das histórias) → Figma (UX) → Jira Cloud (fluxo) → Xray (testes). **Jira e Xray serão descomissionados em favor do Businessmap.** Consequências para este projeto:

- Integração Jira: **fora de escopo permanente**.
- Import Xray XML: **ferramenta de migração com prazo**, não integração contínua. Deve ser feita enquanto há acesso ao Xray.
- Businessmap: única integração externa de longo prazo (último milestone).
- Detalhe de stories vive no Confluence: o requisito local (`.md`) é um espelho resumido criado por colagem manual na v1.

### 1.2 Lição do Probatio

O Probatio falhou por escopo aberto demais e simultâneo demais. Este documento mantém a visão completa, mas o desenvolvimento é fatiado em milestones onde **cada milestone entrega algo usável sozinho**. Se o projeto parar no M1.5, ainda assim resolve a dor principal (rastreabilidade + reporte).

---

## 2. Princípios (invariantes)

1. **Local-first / offline-first.** Nenhuma função central depende de nuvem.
2. **Filesystem é a fonte de verdade.** Banco de dados é índice descartável e reconstruível.
3. **Dados pertencem ao usuário.** Formatos abertos: Markdown, YAML, JSON, Gherkin.
4. **IA é opcional.** A plataforma é 100% funcional sem nenhum provider configurado.
5. **Rastreabilidade nasce no M0.** Não é feature adicionada depois; está embutida no formato dos arquivos.
6. **Adaptadores, não integrações exclusivas.** Automação via interface genérica (Behave hoje, qualquer runner amanhã).
7. **Interface corporativa.** Sem emojis, sem gradientes, densidade de informação alta (referências: GitHub, Linear, Jira Cloud).
8. **Compatibilidade com segundo cérebro.** Os `.md` são legíveis e editáveis no Obsidian sem conversão.

---

## 3. Arquitetura geral

```
┌─────────────────────────────────────────────────┐
│ Frontend — React SPA (Vite)                     │
│ design system próprio, dark, GitHub-like        │
└───────────────┬─────────────────────────────────┘
                │ HTTP (localhost)
┌───────────────▼─────────────────────────────────┐
│ Backend — FastAPI (Python 3.12+)                │
│ ├── Workspace Service (leitura/escrita disco)   │
│ ├── Parser (frontmatter MD + Gherkin)           │
│ ├── Indexer (reindex → SQLite)                  │
│ ├── Execution Engine (manual + subprocess)      │
│ ├── CI Adapter (GitHub Actions API)             │
│ ├── AI Provider (interface + implementações)    │
│ └── Metrics Service (queries no índice)         │
└───────────────┬─────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────┐
│ Filesystem (fonte de verdade)                   │
│ workspace/ + .arbites/index.db (descartável)    │
└─────────────────────────────────────────────────┘
```

Processo único (`uvicorn`), servindo API em `localhost:8347`. Frontend buildado é servido pelo próprio FastAPI como estático (um comando sobe tudo), com dev mode separado via Vite durante desenvolvimento.

### 3.1 Stack

| Camada | Escolha | Justificativa |
|---|---|---|
| Backend | Python 3.12 + FastAPI + Pydantic v2 | Padrão do autor, tipagem forte nos contratos |
| Parser MD | `python-frontmatter` + `markdown-it-py` | Frontmatter YAML + AST para headings |
| Parser Gherkin | pacote oficial `gherkin` | Suporte nativo a `# language: pt` |
| Índice | SQLite (stdlib `sqlite3`) | Zero dependência, descartável |
| Watcher | `watchdog` | Reindex incremental em mudanças no disco |
| Frontend | React 18 + Vite + TypeScript | Kanban drag-and-drop e design system exigem SPA |
| Drag-and-drop | `@dnd-kit/core` | Leve, acessível |
| Gráficos | `recharts` | Suficiente para o dashboard v1 |
| Execução local | `subprocess` (stdlib) | Sem agente separado na v1 |
| Segredos (PAT GitHub) | `keyring` (keychain do OS) | Nunca em arquivo de config |

---

## 4. Workspace — estrutura de pastas

```
workspace/
├── arbites.yaml                     # configuração do workspace
├── requirements/
│   ├── EP-0001-autenticacao.md      # Epic
│   └── ST-0012-login-valido.md      # Story (frontmatter: epic: EP-0001)
├── testcases/
│   ├── frontend/
│   │   └── login/
│   │       ├── CT-0001-login-valido.md
│   │       └── CT-0002-login-invalido.md
│   ├── backend/
│   └── mobile/
├── executions/
│   └── 2026/
│       ├── EXEC-0001/
│       │   ├── execution.json
│       │   └── evidences/
│       │       └── CT-0001/
│       │           ├── screenshot-01.png
│       │           └── log.txt
│       └── EXEC-0002/
└── .arbites/
    ├── index.db                     # SQLite — apagável, `arbites reindex` reconstrói
    └── counters.json                # próximos IDs sequenciais por prefixo
```

Regras:

- Subpastas de `testcases/` são livres (o usuário organiza como quiser); a UI espelha a árvore real.
- Nome de arquivo é livre e não carrega semântica; o ID vive **no frontmatter**. Convenção sugerida `{ID}-{slug}.md` apenas por legibilidade.
- `executions/` particionado por ano para não degradar listagem de diretório.
- Evidências ficam **fora do banco**: o índice guarda apenas caminho relativo, hash SHA-256, tipo MIME e timestamp.
- `.arbites/` inteiro pode entrar no `.gitignore` se o workspace for versionado em git (recomendado).

### 4.1 arbites.yaml

```yaml
workspace:
  name: "QA B3"
  id_prefixes:
    epic: EP
    story: ST
    testcase: CT
    execution: EXEC
    defect: DF

automation_targets:
  - name: frontend-web
    kind: behave
    local_path: "D:/repos/automacao-frontend"     # M3 — execução local
    features_glob: "features/**/*.feature"
    github:                                        # M4 — CI
      repo: "org/automacao-frontend"
      workflow: "tests.yml"
      ref: "main"
      artifact_name: "cucumber-report"

ai:                                                # M5 — tudo opcional
  default_provider: null
  providers: []
```

---

## 5. Formatos de arquivo (contratos)

### 5.1 Requisito — Epic

```markdown
---
id: EP-0001
kind: epic
title: Autenticação
status: active            # active | done | cancelled
external_key: null        # chave no sistema externo (Businessmap futuramente)
tags: [auth]
---

## Descrição

Cobre login, logout, recuperação de senha e MFA.
```

### 5.2 Requisito — Story

```markdown
---
id: ST-0012
kind: story
title: Login com credenciais válidas
epic: EP-0001
status: active            # active | done | cancelled
external_key: "PROJ-123"  # referência textual (Jira hoje, Businessmap depois)
confluence_url: "https://..."   # opcional, link para o detalhe completo
tags: [login]
---

## Resumo

Como usuário cadastrado, quero autenticar com e-mail e senha para acessar o dashboard.

## Critérios de aceite

- WHEN o usuário informa credenciais válidas THEN o sistema exibe o dashboard.
- WHEN o usuário informa senha inválida THEN o sistema exibe mensagem de erro sem revelar qual campo está errado.
```

Critérios de aceite em EARS quando fizer sentido — vira insumo direto para a geração de casos por IA no M5.

### 5.3 Test Case (manual, automated ou hybrid)

```markdown
---
id: CT-0001
title: Login com credenciais válidas
type: hybrid              # manual | automated | hybrid
priority: high            # critical | high | medium | low
status: ready             # draft | ready | deprecated
tags: [login, smoke, regression]
story: ST-0012            # OBRIGATÓRIO para entrar na matriz de cobertura
automation:               # presente apenas se type != manual
  target: frontend-web
  scenario_tag: "@CT-0001"
created: 2026-07-02
updated: 2026-07-02
---

## Objetivo

Validar autenticação com credenciais corretas.

## Pré-condições

- Usuário ativo cadastrado na base de teste.
- Ambiente de homologação disponível.

## Passos

1. Abrir a tela de login.
2. Informar e-mail e senha válidos.
3. Clicar em "Entrar".

## Resultado esperado

Dashboard exibido com o nome do usuário no header.

## Dados de teste

| Campo | Valor |
|---|---|
| email | qa.user@empresa.com |
| senha | (cofre de senhas do time) |
```

Regras do parser:

- Headings `## Passos` e `## Resultado esperado` são âncoras obrigatórias para casos `manual` e `hybrid`; `## Objetivo` e `## Pré-condições` são recomendados. Ausência gera **warning** no reindex, não erro.
- Passos são a lista ordenada sob `## Passos`. A execução manual apresenta cada item como step marcável.
- Caso `automated` puro pode ter corpo mínimo (objetivo apenas); os steps reais vivem no `.feature`.

### 5.4 Feature files (repo de automação, read-only para o Arbites)

O repositório de automação (Selenium + Python + Behave) é **separado** e o Arbites nunca escreve nele. O elo é a tag:

```gherkin
# language: pt
Funcionalidade: Login

  @CT-0001 @smoke
  Cenário: Login com credenciais válidas
    Dado que o usuário está na tela de login
    Quando informar credenciais válidas
    Então deve visualizar o dashboard
```

- Parser: pacote oficial `gherkin`, que resolve `# language:` nativamente (en, pt e todos os demais). Internamente tudo é normalizado para um modelo único (`keyword_type: given|when|then` independente do idioma).
- No reindex, o Arbites escaneia `features_glob` de cada target e monta o mapa `@CT-XXXX → (feature_file, scenario_name, line)`.
- Validações do reindex: tag sem CT correspondente (warning "cenário órfão"), CT `automated`/`hybrid` sem tag encontrada (warning "automação quebrada"), tag duplicada em dois cenários (erro).

### 5.5 execution.json

```json
{
  "schema_version": 1,
  "id": "EXEC-0001",
  "name": "Regressão Sprint 42",
  "owner": "carini",
  "sprint": "Sprint 42",
  "environment": "homolog",
  "origin": "manual",
  "created_at": "2026-07-02T14:00:00-03:00",
  "closed_at": null,
  "status": "in_progress",
  "ci": null,
  "results": [
    {
      "testcase_id": "CT-0001",
      "status": "passed",
      "column": "closed",
      "executed_by": "carini",
      "executed_at": "2026-07-02T14:30:00-03:00",
      "duration_seconds": 240,
      "steps": [
        { "index": 1, "text": "Abrir a tela de login", "status": "passed" },
        { "index": 2, "text": "Informar e-mail e senha válidos", "status": "passed" },
        { "index": 3, "text": "Clicar em \"Entrar\"", "status": "passed" }
      ],
      "evidences": [
        {
          "path": "evidences/CT-0001/screenshot-01.png",
          "sha256": "ab12...",
          "mime": "image/png",
          "captured_at": "2026-07-02T14:29:00-03:00",
          "note": "Dashboard após login"
        }
      ],
      "defects": ["DF-0003"],
      "comment": null,
      "error": null
    }
  ],
  "history": [
    { "at": "2026-07-02T14:00:00-03:00", "who": "carini", "event": "created" },
    { "at": "2026-07-02T14:30:00-03:00", "who": "carini", "event": "result", "testcase_id": "CT-0001", "to": "passed" }
  ]
}
```

Campos de `origin`: `manual` | `local_run` | `github_actions`. Quando `github_actions`, o objeto `ci` guarda `{ "workflow_run_id": 853, "run_url": "...", "commit_sha": "...", "artifact_id": 991 }`.

`sprint` e `environment` são texto livre na v1 (sem cadastro de sprints — evita burocracia).

### 5.6 Defeito (v1 mínima)

Defeito na v1 é um `.md` em `defects/` com frontmatter (`id`, `title`, `status: open|fixed|closed`, `severity`, `testcase`, `execution`, `external_key`). Serve para fechar a ponta da cadeia de rastreabilidade sem construir um bug tracker completo — o bug "de verdade" vive no sistema corporativo, e `external_key` aponta para ele.

---

## 6. Modelo conceitual — separação crítica de estados

Erro comum (presente na discussão original) que este projeto **não** comete: misturar estado do documento com resultado de execução.

| Conceito | Estados | Vive em |
|---|---|---|
| **Test Case** (documento) | `draft` → `ready` → `deprecated` | frontmatter do `.md` |
| **Resultado** (CT dentro de uma execution) | `pending` → `in_progress` → `passed` \| `failed` \| `blocked` \| `retest` → coluna `closed` | `execution.json` |
| **Execution** (o ciclo) | `draft` → `in_progress` → `closed` | `execution.json` |

O mesmo CT-0001 pode estar `passed` na EXEC-0001 e `failed` na EXEC-0002 sem contradição. O Kanban da UI opera sobre **resultados dentro de uma execution**, com colunas: `Pending | In Progress | Blocked | Failed | Retest | Passed`. Arrastar um card atualiza o `execution.json`, grava evento no `history` e reindexa.

---

## 7. Índice SQLite (descartável)

Tabelas (esquema simplificado):

```sql
requirements(id PK, kind, title, epic_id, status, external_key, path, mtime)
testcases(id PK, title, type, priority, status, story_id, path, mtime,
          automation_target, scenario_tag)
tc_tags(testcase_id, tag)
scenarios(target, tag PK, feature_path, scenario_name, line, language)
executions(id PK, name, owner, sprint, environment, origin, status,
           created_at, closed_at, path)
results(execution_id, testcase_id, status, executed_at, duration_seconds,
        PRIMARY KEY(execution_id, testcase_id))
evidences(execution_id, testcase_id, path, sha256, mime, captured_at)
defects(id PK, title, status, severity, testcase_id, execution_id, external_key, path)
warnings(source_path, code, message, created_at)   -- problemas de integridade do reindex
```

### 7.1 Reindex

- **Completo:** varre o workspace inteiro + feature files dos targets. Comando `arbites reindex` (CLI) e botão na UI. Deve rodar em < 5 s para 2.000 CTs.
- **Incremental:** `watchdog` observa o workspace; mudança em arquivo dispara reparse apenas dele. Edições feitas no Obsidian/editor externo aparecem na UI em segundos.
- **Integridade:** o reindex popula `warnings` — story inexistente referenciada, ID duplicado, tag órfã, frontmatter inválido. A UI tem uma tela "Problemas" listando tudo. Warnings não bloqueiam; erro de ID duplicado marca ambos os arquivos como conflito.
- **IDs:** `counters.json` guarda o próximo número por prefixo. Criação via UI/API consome o contador. Arquivo criado à mão com ID manual é aceito; o contador se ajusta no reindex (`max(existente)+1`). Duplicidade é sempre detectada no reindex.

---

## 8. API REST (contrato por milestone)

Base: `http://localhost:8347/api/v1`. Toda resposta de escrita retorna a entidade atualizada. Erros no formato `{ "error": { "code": "...", "message": "..." } }`.

### M0

```
GET    /workspace                      # config + status do índice
POST   /workspace/reindex
GET    /warnings

GET    /tree                           # árvore de pastas de testcases
GET    /requirements?kind=&status=
POST   /requirements
GET    /requirements/{id}
PUT    /requirements/{id}
DELETE /requirements/{id}              # move para .arbites/trash/, nunca apaga direto

GET    /testcases?story=&status=&tag=&type=&folder=&q=
POST   /testcases                      # body inclui folder de destino
GET    /testcases/{id}
PUT    /testcases/{id}
DELETE /testcases/{id}
GET    /testcases/{id}/raw             # markdown cru
PUT    /testcases/{id}/raw             # edição direta do arquivo
```

### M1

```
GET    /executions?sprint=&status=&origin=
POST   /executions                     # body: name, sprint, environment, testcase_ids[]
GET    /executions/{id}
PATCH  /executions/{id}                # status, name, sprint
POST   /executions/{id}/results/{ct}/status    # body: status, comment
POST   /executions/{id}/results/{ct}/steps/{n} # marca step individual
POST   /executions/{id}/results/{ct}/evidences # multipart upload → grava no disco + hash
DELETE /executions/{id}/results/{ct}/evidences/{index}
POST   /executions/{id}/close
GET    /defects | POST /defects | PUT /defects/{id}
```

### M1.5

```
GET    /metrics/summary?sprint=&days=          # cards do topo do dashboard
GET    /metrics/trend?days=7|15|30             # série temporal de resultados
GET    /metrics/coverage                       # cobertura por epic/story
GET    /metrics/traceability?epic=&sprint=     # a MATRIZ (ver §11)
GET    /metrics/flaky?window=5                 # CTs com resultado alternante
```

### M2 (migração Xray)

```
POST   /import/xray                    # multipart XML → preview
POST   /import/xray/confirm            # aplica: gera .md no folder escolhido
POST   /export/markdown?folder=        # zip dos .md (já é o formato nativo)
```

### M3

```
GET    /targets
POST   /targets/{name}/scan            # re-escaneia features
POST   /runs/local                     # body: target, tags|testcase_ids → cria EXEC origin=local_run
GET    /runs/{exec_id}/stream          # SSE: stdout + eventos de step em tempo real
POST   /runs/{exec_id}/cancel
```

### M4

```
POST   /runs/ci                        # body: target, ref, inputs → workflow_dispatch
GET    /runs/ci/{exec_id}/status       # polling consolidado (workflow + jobs + steps)
POST   /runs/ci/{exec_id}/collect      # baixa artifact, parseia, popula results
GET    /settings/github/token          # status apenas (nunca retorna o valor)
PUT    /settings/github/token          # grava no keyring do OS
```

### M5 (IA)

```
GET    /ai/providers | PUT /ai/providers
POST   /ai/generate-testcases          # body: source (story_id | texto | md) → preview de CTs
POST   /ai/review/{testcase_id}        # ambiguidade, duplicidade, passos vagos
POST   /ai/negative-cases/{testcase_id}
```

Toda saída de IA é **preview**: nada é gravado no disco sem confirmação explícita do usuário na UI.

### M6

```
POST   /integrations/businessmap/...   # especificar quando a migração corporativa se concretizar
```

---

## 9. Execução automatizada

### 9.1 Local (M3)

Fluxo:

```
UI seleciona target + filtro (tags ou lista de CTs)
  → POST /runs/local
  → backend monta comando:
      behave -f json -o {tmp}/result.json
             -f plain          # stdout legível para o stream
             --tags=@CT-0001,@CT-0002
             {local_path}
  → subprocess assíncrono (asyncio.create_subprocess_exec)
  → stdout → SSE para a UI (log ao vivo)
  → ao terminar: parse do JSON do Behave → results[] do execution.json
  → evidências capturadas pelos hooks são movidas para evidences/ e hasheadas
```

Regras:

- **Fila:** uma execução local por vez por target (lock por target). Requisições concorrentes entram em fila FIFO visível na UI.
- **Timeout** configurável por target (default 30 min); estouro marca resultados pendentes como `blocked` com `error: "timeout"`.
- Working directory e virtualenv do target são configuráveis (`python_path` no target); o Arbites não gerencia dependências do repo de automação.

### 9.2 Hooks do Behave (contrato de evidências)

Snippet documentado para o usuário adicionar ao `environment.py` do repo de automação:

```python
# environment.py — contrato de evidências Arbites
import os, json
from datetime import datetime, timezone

EVIDENCE_DIR = os.environ.get("ARBITES_EVIDENCE_DIR")  # setado pelo Arbites no run

def after_step(context, step):
    if EVIDENCE_DIR and step.status == "failed" and hasattr(context, "driver"):
        ct = next((t for t in context.scenario.tags if t.startswith("CT-")), "unknown")
        path = os.path.join(EVIDENCE_DIR, ct, f"fail-{step.line}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        context.driver.save_screenshot(path)
```

O Arbites injeta `ARBITES_EVIDENCE_DIR` no ambiente do subprocess (local) ou o workflow publica a pasta como parte do artifact (CI). Sem a variável, os hooks não fazem nada — o repo de automação continua funcionando sozinho.

### 9.3 GitHub Actions (M4)

**Restrição real da API (corrige a suposição da discussão original):** logs completos de um job só ficam disponíveis via API **após o término do job**. O que existe ao vivo é o status de workflow/jobs/steps do *workflow* (Checkout, Setup Python, Execute Tests...), não dos steps *Gherkin*. O design assume isso:

1. **Trigger:** `POST /repos/{repo}/actions/workflows/{workflow}/dispatches` com `ref` e `inputs` (ex.: `tags: "@CT-0001"`). A API não retorna o run id — o Arbites correlaciona buscando o run mais recente do workflow criado após o dispatch (janela de 30 s, filtro por `event: workflow_dispatch`).
2. **Acompanhamento:** polling a cada 10 s em `/actions/runs/{id}` e `/actions/runs/{id}/jobs`. A UI mostra a timeline dos steps do workflow com status ao vivo (`queued → in_progress → completed`), estilo tela do próprio GitHub.
3. **Coleta:** ao `completed`, baixa o artifact configurado (`artifact_name`), extrai o **Cucumber JSON** (o workflow deve rodar `behave -f json`), parseia e popula `results[]` — mesmíssimo parser do run local. Evidências dentro do artifact são movidas para `evidences/`.
4. **Requisito no repo de automação:** o workflow precisa (a) aceitar `workflow_dispatch` com input de tags e (b) publicar o JSON + screenshots como artifact. O documento do M4 inclui um `tests.yml` de exemplo.

**Alternativa registrada (ADR):** self-hosted runner na máquina local — o trigger vem do GitHub, a execução roda localmente com acesso ao ambiente, e o resultado aparece no GitHub nativamente. Não entra na v1, mas o design de coleta por artifact funciona igual nos dois casos.

**Token:** PAT fine-grained com escopo mínimo (`actions:read+write` no repo do target), armazenado via `keyring` no cofre do SO. Nunca em YAML, nunca no índice, nunca logado.

---

## 10. Migração Xray (M2 — janela de tempo)

Como o Xray será descomissionado, este utilitário tem prioridade acima da automação:

- Input: XML de export do Xray (test repository + testes com steps).
- Mapeamento: `Test → CT .md` (steps → `## Passos`, prerequisites → `## Pré-condições`), labels → tags, prioridade → prioridade. Vínculo com requisito: se o XML trouxer a issue key da story, ela vira `external_key` e o usuário decide na UI de preview se cria a story local correspondente.
- Fluxo em duas etapas: **preview** (tabela do que será criado, conflitos de ID, campos não mapeáveis) → **confirm** (gera os `.md`).
- Idempotente: reimportar o mesmo XML detecta CTs já migrados por `external_key` e pula.

---

## 11. Dashboard e matriz de rastreabilidade (M1.5)

Público-alvo: **superiores**. Métricas escolhidas por serem defensáveis em reunião, com fórmula explícita:

| Métrica | Fórmula | Filtros |
|---|---|---|
| Cobertura de requisito | stories `active` com ≥1 CT `ready` ÷ stories `active` | epic |
| Cobertura de execução | CTs distintos executados no período ÷ CTs `ready` | sprint, período |
| Pass rate | resultados `passed` ÷ resultados finais (`passed`+`failed`) | sprint, período, target |
| Taxa de bloqueio | `blocked` ÷ total de resultados | idem |
| Retrabalho | resultados que passaram por `retest` ÷ total | idem |
| Instabilidade (flaky) | CTs cujo resultado alternou pass/fail nas últimas N execuções | janela N |
| Tendência | série diária de passed/failed/blocked | 7 / 15 / 30 dias |

**Matriz de rastreabilidade** (a tela principal para chefia):

```
Epic → Story | CTs | Último resultado | Execution | Evidências | Defeitos
─────────────────────────────────────────────────────────────────────────
EP-0001 Autenticação
  ST-0012 Login válido      3 CTs   ● passed    EXEC-0102   2 arquivos   —
  ST-0013 Recuperar senha   1 CT    ● failed    EXEC-0102   1 arquivo    DF-0003
  ST-0014 MFA               0 CTs   ○ sem cobertura
```

Cada célula é clicável até chegar no arquivo de evidência. Exportação da matriz: **PDF e Markdown** (para colar no Confluence) — isso é parte do M1.5, porque o reporte para cima é a dor declarada número um.

---

## 12. IA (M5)

Interface única:

```python
class AIProvider(Protocol):
    async def complete(self, system: str, user: str,
                       schema: type[BaseModel] | None = None) -> str | BaseModel: ...
```

Implementações: OpenAI, Anthropic, Gemini, OpenRouter, Ollama, LM Studio, vLLM. As três últimas via base URL OpenAI-compatível — na prática são **uma** implementação (`OpenAICompatible`) com URLs diferentes, o que reduz os 7 providers a ~4 classes. Config no `arbites.yaml`, chaves no keyring.

Funções (todas com preview obrigatório antes de gravar):

1. **Gerar CTs a partir de story** — input: `.md` da story (idealmente com critérios EARS); output: lista de CTs em schema Pydantic validado, apresentados como diff/preview.
2. **Revisar CT** — detecta passos ambíguos, duplicidade contra o índice (busca por título/tags similares), resultado esperado vago.
3. **Casos negativos** — a partir de um CT positivo, propõe variações (campos vazios, caracteres especiais, limites).

Nota de contexto local: LM Studio com backend Vulkan é o caminho testado no hardware do autor (RDNA4); Ollama está fora por incompatibilidade conhecida.

---

## 13. Frontend e design system

React SPA. Telas por milestone:

| Milestone | Telas |
|---|---|
| M0 | Árvore do repositório, editor de CT (form + aba markdown cru), lista/editor de requisitos, tela Problemas (warnings) |
| M1 | Lista de executions, tela de execução (Kanban + painel do CT com steps marcáveis + upload de evidência), defeitos |
| M1.5 | Dashboard, matriz de rastreabilidade, export PDF/MD |
| M2 | Wizard de import Xray (upload → preview → confirm) |
| M3 | Tela de run local (log SSE ao vivo, fila) |
| M4 | Tela de run CI (timeline de steps do workflow, botão collect) |
| M5 | Configuração de providers, previews de geração/revisão |

Tokens do design system:

```
Background   #0D1117      Primary  #2F81F7
Surface      #161B22      Success  #238636
Border       #30363D      Warning  #D29922
Text         #E6EDF3      Danger   #DA3633
Text muted   #8B949E      Retest   #A371F7
Fonte UI     Inter
Fonte mono   JetBrains Mono (IDs, paths, logs, gherkin)
```

Regras: sem emojis, sem gradientes, cards densos com bordas de 1px, espaçamento em múltiplos de 4px, densidade de tabela estilo Linear. Status sempre com ponto colorido + texto (nunca só cor — acessibilidade).

---

## 14. Milestones — escopo e critério de pronto

### M0 — Fundação
Escopo: workspace, `arbites.yaml`, parsers (frontmatter + headings), reindex completo e incremental, contadores de ID, API de requisitos/testcases, árvore na UI, editor de CT, tela de warnings.
**Pronto quando:** criar epic, story e CT pela UI; editar o mesmo CT no Obsidian e ver a mudança refletida na UI sem ação manual; apagar `index.db`, rodar reindex e nada se perder.

### M1 — Execução manual
Escopo: executions, Kanban de resultados, steps marcáveis, upload de evidências com hash, histórico de eventos, defeitos mínimos, fechamento de execution.
**Pronto quando:** rodar uma regressão manual completa de ~20 CTs, com evidências anexadas e um defeito vinculado, sem tocar em outro sistema.

### M1.5 — Dashboard e rastreabilidade
Escopo: as 7 métricas, tendência, matriz de rastreabilidade navegável, export PDF/Markdown.
**Pronto quando:** gerar um reporte de sprint apresentável a um gestor em < 1 minuto, com drill-down até a evidência.

### M2 — Migração Xray
Escopo: import XML com preview e idempotência; export Markdown.
**Pronto quando:** a base real do Xray da B3 estiver migrada para um workspace local.

### M3 — Automação local
Escopo: targets, scan de features, run via subprocess com SSE, fila, parse do JSON do Behave, evidências via hooks, vínculo `@CT-XXXX`.
**Pronto quando:** disparar a automação real de frontend pela UI, ver o log ao vivo e a execution populada com steps Gherkin e screenshots de falha.

### M4 — GitHub Actions
Escopo: workflow_dispatch, correlação de run, polling de status, coleta de artifact, PAT no keyring, `tests.yml` de exemplo.
**Pronto quando:** disparar o workflow real pela UI, acompanhar os steps do workflow e, ao fim, ter a execution idêntica à de um run local.

### M5 — IA
Escopo: providers, geração de CTs, revisão, casos negativos, tudo com preview.
**Pronto quando:** gerar CTs a partir de uma story real com LM Studio local e com um provider cloud, e aceitar/rejeitar item a item.

### M6 — Businessmap
Escopo: a definir quando a migração corporativa se concretizar. Direção: import read-only de cards → requisitos locais (`external_key`), export opcional de resultados como comentário/anexo no card.

---

## 15. Decisões registradas (ADRs resumidos)

| # | Decisão | Alternativa rejeitada | Motivo |
|---|---|---|---|
| 1 | Filesystem fonte de verdade + SQLite índice descartável | DB como fonte | Portabilidade, Obsidian, zero lock-in; métricas precisam de índice |
| 2 | ID no frontmatter, nome de arquivo livre | ID no nome do arquivo | Rename/move não quebra vínculos |
| 3 | Vínculo CT↔cenário por tag `@CT-XXXX` | Convenção por nome/caminho | Explícito, estável, sobrevive a refactor do repo de automação |
| 4 | Subprocess direto na v1 | Agente separado | Overengineering para plataforma local; agente só quando houver execução remota própria |
| 5 | Status de documento ≠ status de resultado | Ciclo único misto | Mesmo CT com resultados diferentes em executions diferentes |
| 6 | Coleta CI por artifact (Cucumber JSON) | Logs ao vivo por step Gherkin | API do GitHub não fornece log de job em andamento |
| 7 | Jira fora de escopo; Xray como migração pontual | Integração contínua | Descomissionamento corporativo confirmado |
| 8 | PAT no keyring do OS | Arquivo de config | Segredo nunca em texto plano no workspace |
| 9 | React SPA | Jinja+HTMX | Kanban drag-and-drop e densidade de UI exigem SPA; padrão do autor |
| 10 | Sprint/ambiente como texto livre na v1 | Cadastro de sprints | Reduz burocracia; estrutura pode vir depois sem migração de dados |

## 16. Fora de escopo da v1 (explícito)

- Multiusuário, autenticação, permissões (plataforma é single-user local; colaboração = git no workspace).
- Bug tracker completo (defeito é ponteiro + metadados).
- Cadastro de sprints/releases.
- Execução distribuída / agentes remotos.
- Integração Jira (permanente), Businessmap (adiado para M6), Confluence (link manual).
- Edição de feature files pela plataforma (repo de automação é read-only).
- Telemetria de qualquer tipo.

## 17. Riscos

| Risco | Mitigação |
|---|---|
| Escopo inchar de novo (síndrome Probatio) | Critério de pronto por milestone; nada do milestone N+1 começa antes do N fechar |
| Workspace corrompido por edição externa inválida | Reindex tolerante + tela de warnings; arquivos inválidos são listados, nunca silenciosamente ignorados |
| Perda da janela de migração do Xray | M2 posicionado cedo; export do XML pode ser feito já, antes mesmo do M2 existir |
| API do GitHub mudar/limitar polling | Rate limit tratado com backoff; alternativa self-hosted runner registrada no ADR 6 |
| Behave mudar formato JSON | Parser isolado atrás da interface de adapter; testes de contrato com JSONs de exemplo versionados |