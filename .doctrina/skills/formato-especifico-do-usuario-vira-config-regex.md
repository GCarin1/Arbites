---
name: formato-especifico-do-usuario-vira-config-regex
description: Quando um recurso depende de um formato de string específico da organização do usuário (nome de run, convenção de branch, padrão de arquivo), NÃO hardcode o formato — extraia com uma regex configurável (grupos nomeados) em arbites.yaml, com um default genérico e degradação graciosa quando nada casa. Mantém o produto white-label.
when: Ao implementar uma feature que precisa "entender" um texto cuja estrutura vem da convenção interna do cliente (nome de execução CI, tag de release, path de artefato) — especialmente num produto que deve servir qualquer empresa/projeto.
---

# Skill — formato-especifico-do-usuario-vira-config-regex

## When to use this skill

- A feature precisa extrair partes de uma string cuja ESTRUTURA é definida
  pela convenção da organização do usuário (ex.: nome de run CI
  `"<nome> . <org>/<repo>.<env>"`, branch `release/x.y`, artefato
  `logs/<data>/<suite>.json`).
- O produto deve funcionar para QUALQUER empresa/projeto (white-label) — o
  código não pode conter o formato de um cliente específico.

## Princípio

Formato específico do cliente = **dado de configuração**, não constante de
código. Uma regex com grupos nomeados no arquivo de config é o ponto de
extensão certo: o cliente descreve a própria convenção sem tocar no código, e
o repositório permanece neutro.

## Procedure

1. **Regex configurável com grupos nomeados** em `arbites.yaml`
   (ex.: `ci_monitoring.name_pattern` com `(?P<repo>…)` e `(?P<env>…)`).
   Documente quais grupos são obrigatórios vs opcionais.
2. **Default genérico** que resolve o caso comum SEM citar nenhum cliente —
   uma regex é neutra por natureza; escolha um separador comum e deixe
   sobrescrevível. Nunca coloque o nome/domínio de uma empresa no default.
3. **Degradação graciosa:** o que não casa vira um contador (`unparsed`) e um
   hint na UI ("configure o padrão X") — não um erro nem um silêncio. O
   usuário precisa saber que há dados fora do padrão e como corrigir.
4. **Regex inválida não derruba a rota:** compile em try/except; ao falhar,
   caia no default e devolva `pattern_error` para a UI exibir. Uma config
   ruim do usuário não pode dar 500 numa tela de leitura.
5. **Peça um exemplo real do formato** ao usuário e teste a regex contra ele
   (e contra uma variação genérica de outra empresa) ANTES de fechar — foi
   assim que o default foi validado sem hardcodar o caso do cliente.

## Anti-patterns

- `if "nomedocliente" in name:` — amarra o produto a um cliente.
- Hardcodar o separador/estrutura como constante de código sem override.
- Silenciar o que não casa (some do relatório sem explicação) — o usuário
  acha que a feature está quebrada.
- Deixar uma regex de config inválida propagar como 500.

## Related material

- `backend/arbites/metrics.py` — `DEFAULT_CI_NAME_PATTERN`,
  `automation_report` (grupos `repo`/`env`, `unparsed`, `pattern_error`).
- `backend/arbites/api.py` — `GET /metrics/automation` lê
  `ci_monitoring.name_pattern`.
- `frontend/src/components/Dashboard.tsx` — `AutomationPanel` (hint de config).
- Spec `reporting` (#8).
