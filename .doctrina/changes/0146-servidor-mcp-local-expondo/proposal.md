# Change 0146-servidor-mcp-local-expondo — servidor MCP local expondo as leituras derivadas que um agente nao consegue calcular sozinho

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** mcp-server

## Why

servidor MCP local expondo as leituras derivadas que um agente nao consegue calcular sozinho

## What

Abre a capability `mcp-server` com as ferramentas de **leitura**.

A tentação óbvia — e o erro — seria envelopar a REST inteira em MCP. O
agente já sabe chamar HTTP e já sabe ler arquivo. O que ele não tem é a
resposta **derivada**, e é só isso que entra:

| ferramenta | responde | fonte que já existe |
|---|---|---|
| `coverage_gaps` | stories e critérios EARS sem caso | `coverage_state` (0087) + `critCovered/critTotal` (0092) |
| `impact_of_files` | casos afetados por arquivos alterados | tag `@CT-XXXX` (ADR 0003) + mapa de risco |
| `pending_rerun` | casos esperando re-execução | flag `needs_rerun` (0090) |
| `context_pack` | o bundle de um escopo | `/context-pack` |
| `execution_report` | resultado + evidência de um ciclo | executions + evidences |
| `external_links` | o que daqui está ligado a quê lá | change 0145 |

`impact_of_files` é a que só existe porque o agente segura as três pontas:
GitHub MCP dá o diff, esta ferramenta diz quais casos aquele diff toca, e o
agente leva a lista para o card e para o PR. **Vínculo explícito por tag e
correlação por risco voltam separados** — são confianças diferentes, e
misturá-las faria o agente tratar palpite como fato.

Os artefatos também saem como **recursos** com URI (`arbites://testcase/CT-0007`),
não só como retorno de tool: aí o agente referencia sem recolar corpo inteiro
na conversa.

O servidor é processo local que fala HTTP com a instância, carregando uma
sessão real — então papel, módulo desligado e log de atividade (ADR 0014)
valem de graça, e a auditoria mostra em nome de quem o agente agiu.

**Afeta spec:** `mcp-server` (nova). **ADR:** 0015.

## Scope boundaries

- Só leitura. Nenhuma ferramenta desta change altera o workspace.
- Não implementa conector para ferramenta externa nenhuma — quem atravessa
  é o agente.
- Não desenha a tela de configuração (change 0149).
- Não inventa endpoint novo de backend para servir o MCP: se a resposta
  derivada ainda não existe na API, ela nasce como rota normal e o MCP a
  consome, para não criar um caminho paralelo que ninguém audita.

## Verification

<!--
How you will know the change is correctly applied. Use checkboxes: every
box here is a claim that must be PROVEN before the change is done.
`doctrina change archive` refuses to archive while any box below is
unchecked (pass --force to archive anyway and record the gap). Distinguish
"task marked done" from "verification passed" — link the evidence.
-->

- [ ] Automated checks pass (`doctrina verify`, or the project's typecheck/test/build).
- [ ] The affected spec's acceptance criteria are met and cite their evidence (`doctrina coverage`).
- [ ] Um cliente MCP real (Cursor ou equivalente) lista as ferramentas e
      obtém as lacunas de cobertura de uma story semeada.
- [ ] `impact_of_files` devolve vínculo por tag e correlação por risco em
      campos separados.
- [ ] Módulo desligado faz a ferramenta MCP recusar com o mesmo código da
      rota HTTP.
- [ ] Toda chamada aparece no log de atividade com a conta de origem.

## Open questions

Nenhuma.
