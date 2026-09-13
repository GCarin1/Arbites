# Design — página do MCP (aba de IA)

## Onde mora e por quê

Sub-aba **MCP** dentro de `Assistente de IA`, ao lado de Gerar · Revisar ·
Context Pack · Configuração. Faz sentido ali porque é a mesma pergunta das
outras: *"como a IA alcança o meu trabalho?"*. A faixa de abas rola desde a
change 0135, então a quinta aba cabe sem apertar nada.

## Interruptor: superfície, não módulo

O servidor MCP entra em `SWITCHES` como **`mcp_server`** (superfície
perigosa), **não** em `MODULES`. O critério da ADR 0014 é claro: módulo
governa uma TELA, superfície governa uma CAPACIDADE técnica. Publicar o
workspace para um processo externo é capacidade, não tela — e a tela precisa
continuar visível justamente para poder religar.

Com `mcp_server` desligado, o servidor recusa toda ferramenta e a página
mostra isso como estado, não como erro.

## A página, de cima para baixo

### 1. Estado do servidor

Cartão de cabeçalho, primeira coisa que se lê:

- interruptor `mcp_server` (o mesmo toggle do painel — um controle, um estado)
- endereço que o agente deve usar: `http://<host>:<porta>`
- última chamada recebida, e de qual conta
- se nunca houve chamada: **estado de primeiro uso**, não caixa vazia —
  título, o que é o MCP em duas linhas, e a ação "Gerar credencial".

### 2. Como conectar  *(o item mais útil da página)*

Bloco de configuração pronto para colar no cliente MCP, com botão de copiar
e um seletor de cliente (Cursor · Claude Desktop · genérico), porque o
caminho do arquivo de config muda entre eles:

```json
{
  "mcpServers": {
    "arbites": {
      "command": "arbites-mcp",
      "env": {
        "ARBITES_URL": "http://192.168.0.17:8347",
        "ARBITES_TOKEN": "<gerado abaixo>"
      }
    }
  }
}
```

O bloco é código e pode estourar a largura no celular: vai dentro do
utilitário `.scroll-x` (change 0138), que já dá rolagem com sombra de borda.

### 3. Credencial do agente

Token **separado da sessão do navegador**, gerado aqui, com nome e
revogação. Separado de propósito: revogar o acesso do agente não pode
derrubar a sua sessão, e a recíproca também vale.

- herda o **papel da conta** que o gerou — o agente nunca alcança mais que
  a pessoa;
- mostrado **uma vez** na criação (padrão de PAT), com aviso claro;
- lista mostra nome, criado em, último uso, e "Revogar".

### 4. O que o agente alcança

Duas listas, separadas por efeito:

**Leitura** — `coverage_gaps`, `impact_of_files`, `pending_rerun`,
`context_pack`, `execution_report`, `external_links`.
**Escrita** — `create_or_update_testcase`, `record_result`, `link_external`.

Cada uma com uma linha do que faz. E **um toggle único: "permitir escrita"**,
desligado por padrão.

Toggle por ferramenta seria granularidade falsa: a pergunta real que alguém
faz é "esse agente pode mexer no meu repositório ou só olhar?", e essa
pergunta tem duas respostas, não nove. Se um dia houver demanda de recorte
mais fino, ele nasce de um caso concreto, não de suposição.

### 5. Últimas chamadas do agente

As últimas N entradas do log de atividade filtradas por origem MCP: quando,
qual ferramenta, qual conta, e o que mudou. É o que transforma "confio no
agente" em "vejo o que o agente fez". Reusa o log que já existe — nada novo
no backend.

### 6. Vínculos externos

Uma linha de resumo ligando esta página à capability `integrations`:

> 47 casos ligados a `businessmap` · **3 em conflito** →

O contador de conflito leva para a tela Problemas, que é onde o conflito
mora (ADR 0015). Sem isso a pessoa só descobre conflito por acaso.

## Estados

- **Nunca conectado** → primeiro uso: o que é, e "Gerar credencial".
- **`mcp_server` desligado** → estado explicando que está desligado, com o
  toggle ali mesmo. Não é erro.
- **Sem permissão** (papel não-admin) → a página mostra o estado e as
  ferramentas, mas o toggle e a geração de credencial ficam indisponíveis,
  com o motivo escrito. Ver a configuração da instância não é privilégio;
  mudá-la é.

## O que esta página NÃO é

- Não é um console para chamar ferramenta MCP na mão. Quem chama é o agente;
  um playground aqui seria uma segunda porta para auditar.
- Não duplica o painel de administração: o toggle é o mesmo objeto, exibido
  onde a pergunta nasce.
