# Change 0149-pagina-mcp-aba-ia — pagina do MCP na aba de IA com estado do servidor instrucoes de conexao ferramentas expostas e vinculos externos

- **Status:** proposed
- **Date:** 2026-09-13
- **Owner:**
- **Lane:** product (uncertain)
- **Affects specs:** ai-assist

## Why

pagina do MCP na aba de IA com estado do servidor instrucoes de conexao ferramentas expostas e vinculos externos

## What

A sub-aba **MCP** dentro de `Assistente de IA` — o lugar onde se liga o
servidor, se gera a credencial do agente, se vê o que ele alcança e o que
ele já fez. O desenho completo está em `design.md`, ao lado desta proposta.

Resumo do que ela resolve:

- **Conectar** deixa de ser "leia a documentação": o bloco de configuração
  sai pronto para colar, por cliente (Cursor · Claude Desktop · genérico).
- **Credencial própria do agente**, separada da sessão do navegador, com
  revogação — revogar o agente não pode derrubar a sua sessão.
- **Uma decisão de permissão, não nove**: um toggle "permitir escrita",
  desligado por padrão. A pergunta que as pessoas fazem é "ele mexe ou só
  olha?", e ela tem duas respostas.
- **Trilha visível**: as últimas chamadas do agente, do log de atividade que
  já existe. É o que transforma "confio" em "vejo".
- **Ponte para o conflito**: o contador de vínculos externos leva para
  Problemas quando há conflito de sincronia.

O servidor entra como `mcp_server` em **SWITCHES** (superfície perigosa), não
em MODULES: pelo critério da ADR 0014, publicar o workspace para um processo
externo é capacidade, não tela — e a tela precisa seguir visível para poder
religar.

**Afeta spec:** `ai-assist`. **ADR:** 0014 (interruptor), 0015 (integração).

## Scope boundaries

- Não é console de MCP: não se chama ferramenta na mão por aqui. Quem chama
  é o agente, e um playground seria uma segunda porta para auditar.
- Não duplica o painel de administração — o toggle é o mesmo objeto,
  mostrado onde a pergunta nasce.
- Não implementa as ferramentas MCP (changes 0146 e 0147); aqui é a tela.

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
- [ ] O bloco de configuração é copiável e traz o endereço real da
      instância, não um placeholder.
- [ ] A credencial aparece uma única vez e pode ser revogada sem derrubar a
      sessão do navegador.
- [ ] Com "permitir escrita" desligado, uma ferramenta de escrita é recusada.
- [ ] Conta não-admin vê o estado e as ferramentas, e não consegue mudar o
      interruptor nem gerar credencial — com o motivo escrito.
- [ ] Em 390 px o bloco de configuração rola dentro de si e a página não
      rola de lado.

## Open questions

Nenhuma.
