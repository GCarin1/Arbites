---
name: configuracao-que-a-tela-nao-alcanca
description: Toda configuração que uma funcionalidade EXIGE precisa de campo na tela; sem isso o erro correto ("falta X no arquivo") não tem onde ser resolvido, e um modelo Pydantic sem o campo ainda APAGA o que foi escrito à mão no arquivo ao salvar pela tela.
when: O agente vai ler ou escrever um bloco de `arbites.yaml` a partir da API, ou está diagnosticando um erro de "não configurado" que o usuário não consegue resolver.
---

# Skill — configuração que a tela não alcança

## When to use this skill

- Uma rota recusa por falta de configuração (`no_github`, `no_sources`,
  `no_token`) e o usuário responde "mas onde eu configuro isso?".
- O agente vai adicionar uma chave a `arbites.yaml` consumida pelo backend.
- Um `PUT` reserializa um bloco inteiro do YAML a partir de um modelo
  Pydantic (`PUT /targets`, `PUT /ai/providers`, `PUT /ci/sources`).

## Procedure

1. Antes de acrescentar uma chave ao `arbites.yaml`, responda: **qual tela
   escreve isto?** Se a resposta for "nenhuma, o usuário edita à mão", o
   recurso nasce inalcançável para quem não abre o arquivo.
2. Se já existe um `PUT` que reserializa o bloco, o campo novo **tem** de
   entrar no modelo Pydantic. `model_dump()` de um modelo sem o campo
   descarta o que estava no arquivo — em silêncio, sem erro nenhum.
   Prove com um teste de ida e volta: gravar, ler, gravar o que leu, e
   conferir que o valor sobreviveu às duas gravações.
3. Na mensagem de recusa, nomeie a **tela**, não a chave do arquivo:
   "Preencha os dois em Automação → Configurar" resolve; "target sem bloco
   github (repo/workflow)" só descreve.
4. Bloco pela metade é pior que bloco ausente — um `github: {repo: x,
   workflow: ""}` faz o erro acusar falta de configuração com o bloco
   aparentemente presente no YAML. Descarte o incompleto na gravação.
5. Campo opcional em branco não vira chave com `""`: ausente costuma
   significar "todos", e `""` faz o backend procurar um nome vazio.
6. Escrita no `arbites.yaml` é superfície governada: entre na tabela
   `_GOVERNED` como `admin`. Leitura fica aberta — a tela precisa dizer
   "nada declarado" também a quem não pode declarar.

## Anti-patterns

- Documentar a chave no README e considerar o recurso entregue. O README não
  está aberto na hora em que a pessoa clica no botão e não acontece nada.
- Testar só o caminho feliz do `PUT`. O defeito das changes 0167–0172 era
  invisível numa gravação só: aparecia na SEGUNDA, quando a tela devolvia o
  alvo sem o bloco que ela própria não conhecia.
- Tratar o vazio como valor.

## Related material

- `.doctrina/changes/archive/2026-09-15-0172-bloco-github-alvo-existe/`
- `.doctrina/changes/archive/2026-09-15-0173-origens-observabilidade-so-existem/`
- [Workflow](../../docs/en/workflow.md)
