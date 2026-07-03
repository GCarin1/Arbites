# Arbites — Product

## Vision

Arbites é uma plataforma local-first de gestão e rastreabilidade de testes,
executada inteiramente na máquina do usuário, cujo diferencial central é a
cadeia de rastreabilidade completa: Epic → Story → Test Case → Execution →
Evidência → Defeito. O objetivo não é replicar Xray/Zephyr feature a
feature, mas responder com prova as perguntas da chefia: "essa história foi
validada?", "qual execução encontrou a falha?", "quais evidências comprovam
a aprovação?", "qual a cobertura e o pass rate da sprint?". Tudo que existe
na interface existe no disco — a UI é uma visualização da estrutura real de
arquivos.

## Problem

O fluxo corporativo atual (Miro → Confluence → Figma → Jira Cloud → Xray)
está sendo descomissionado: Jira e Xray sairão em favor do Businessmap, que
não cobre gestão de testes. O QA fica sem ferramenta de rastreabilidade e
sem forma defensável de reportar cobertura, pass rate e evidências para a
gestão. O antecessor deste projeto (Probatio) falhou por escopo aberto e
simultâneo demais; Arbites mantém a visão completa mas entrega em
milestones onde cada um é usável sozinho.

## Target users

- O próprio autor (QA na B3), usuário único da v1: gerencia casos de teste
  manuais e automatizados (Selenium + Behave) e reporta para gestão.
- Secundariamente, a gestão/chefia como consumidora dos reportes (matriz de
  rastreabilidade, dashboard exportado em PDF/Markdown).

## Scope

In scope:

- Workspace em filesystem (Markdown/YAML/JSON/Gherkin) como fonte de
  verdade; SQLite como índice descartável e reconstruível.
- CRUD de requisitos (epic/story), casos de teste e defeitos mínimos via
  API REST local (FastAPI, `localhost:8347`) e React SPA.
- Execução manual: executions, Kanban de resultados, steps marcáveis,
  evidências com hash SHA-256, histórico de eventos.
- Dashboard com 7 métricas defensáveis + matriz de rastreabilidade com
  export PDF/Markdown.
- Migração pontual do Xray (import XML com preview, idempotente) — janela
  de tempo antes do descomissionamento.
- Automação local via subprocess (Behave, vínculo por tag `@CT-XXXX`, log
  SSE ao vivo) e via GitHub Actions (workflow_dispatch + coleta de
  artifact Cucumber JSON).
- IA opcional (geração/revisão de CTs, casos negativos), sempre com
  preview antes de gravar; providers OpenAI-compatíveis + Anthropic +
  Gemini.

Out of scope (deferred or rejected):

- Multiusuário, autenticação, permissões (single-user local; colaboração =
  git no workspace).
- Bug tracker completo (defeito é ponteiro + metadados; o bug real vive no
  sistema corporativo via `external_key`).
- Cadastro de sprints/releases (texto livre na v1).
- Execução distribuída / agentes remotos.
- Integração Jira (permanente — descomissionada), Confluence (link
  manual), Businessmap (adiada para M6, especificar quando a migração
  corporativa se concretizar).
- Edição de feature files pela plataforma (repo de automação é read-only).
- Telemetria de qualquer tipo.

## Non-goals

- Não é um clone de Xray/Zephyr nem um substituto de Jira.
- Não é uma plataforma cloud/SaaS: nenhuma função central depende de nuvem.
- Não é dependente de IA: 100% funcional sem nenhum provider configurado.
- Não gerencia o repositório de automação (dependências, código, CI dele).

## Success criteria

- [SC1] Criar epic, story e CT pela UI; editar o mesmo CT no Obsidian e ver
  a mudança refletida na UI sem ação manual; apagar `index.db`, reindexar e
  nada se perder. (M0)
- [SC2] Rodar uma regressão manual completa de ~20 CTs, com evidências
  anexadas e um defeito vinculado, sem tocar em outro sistema. (M1)
- [SC3] Gerar um reporte de sprint apresentável a um gestor em menos de 1
  minuto, com drill-down até o arquivo de evidência. (M1.5)
- [SC4] Migrar a base real do Xray da B3 para um workspace local antes do
  descomissionamento. (M2)
- [SC5] Disparar a automação real de frontend pela UI, ver o log ao vivo e
  a execution populada com steps Gherkin e screenshots de falha. (M3)
- [SC6] Disparar o workflow real no GitHub pela UI, acompanhar os steps e
  obter uma execution idêntica à de um run local. (M4)
- [SC7] Gerar CTs a partir de uma story real com LM Studio local e com um
  provider cloud, aceitando/rejeitando item a item. (M5)
- [SC8] Reindex completo em menos de 5 segundos para 2.000 CTs.

## Delivery order (walking skeleton)

Depth before breadth — o esqueleto é o M0 de ponta a ponta:

1. **Walking skeleton (M0):** workspace no disco → parser
   (frontmatter/headings) → reindex para SQLite (completo + incremental via
   watchdog) → API REST de requisitos/testcases → UI com árvore, editor de
   CT e tela de warnings. Verificado quando SC1 passa.
2. M1 — execução manual (executions, Kanban, steps, evidências, defeitos).
3. M1.5 — dashboard, matriz de rastreabilidade, export PDF/MD.
4. M2 — migração Xray (prioridade acima da automação: janela de tempo).
5. M3 — automação local (subprocess + SSE).
6. M4 — GitHub Actions.
7. M5 — IA opcional.
8. M6 — Businessmap (especificar quando se concretizar).

Nada do milestone N+1 começa antes do N fechar (lição do Probatio).
