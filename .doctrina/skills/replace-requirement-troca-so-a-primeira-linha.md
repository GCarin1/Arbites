---
name: replace-requirement-troca-so-a-primeira-linha
description: O op `replace-requirement` de um delta troca apenas a PRIMEIRA linha do bullet alvo — as linhas de continuação de um requisito quebrado em várias linhas sobrevivem e viram texto órfão dentro da spec, sem que analyze, apply ou validate reclamem.
when: O agente vai escrever um bloco ops com `replace-requirement` (ou qualquer op que reescreva um bullet) numa spec cujos requisitos estão quebrados em várias linhas.
---

# Skill — replace-requirement troca só a primeira linha

## When to use this skill

- O agente está escrevendo `.doctrina/changes/<id>/specs/<cap>/delta.md` com
  um bloco ```ops``` que contém `replace-requirement <secao> <n>: ...`.
- A spec alvo tem requisitos escritos em várias linhas (o estilo antigo de
  `auth`, `workspace-core`, `executions`), e não uma linha longa por bullet.

## Procedure

1. Antes de escrever o op, olhe o bullet que vai ser trocado:
   `sed -n '/### Event-driven/,/^### /p' .doctrina/specs/<cap>/spec.md`
2. Conte as linhas do bullet. **Uma linha** → `replace-requirement` resolve.
   **Duas ou mais** → o op deixa as linhas 2..n órfãs; planeje a limpeza.
3. Rode `doctrina analyze <id>` e leia o "N ops would apply cleanly": ele
   confere que o op ENCONTRA o alvo, não que o resultado fique coerente.
4. Depois de `doctrina change apply` ou `doctrina close`, **leia a seção
   alterada da spec**, não só a saída do gate:
   `sed -n '/### <secao>/,/^### /p' .doctrina/specs/<cap>/spec.md`
5. Se sobraram linhas órfãs, apague-as direto na spec (spec é a verdade
   corrente, editar é legítimo) e rode `doctrina validate`.

## Anti-patterns

- Confiar no `✓ N ops would apply cleanly` do `analyze` como prova de que a
  spec ficou correta. Ele prova que o alvo foi localizado, nada além disso.
- Fechar a change (`doctrina close`) sem reler o trecho tocado: os gates
  passam com o texto órfão dentro, porque uma linha de continuação solta é
  Markdown válido e não é um bullet EARS — ninguém a examina.
- "Corrigir" abrindo uma change nova só para apagar as sobras: a spec já é a
  verdade corrente; apague e valide.

## Related material

- `.doctrina/changes/archive/2026-09-14-0168-cadastro-formulario-fica-pendente/`
  — onde isto aconteceu, na seção Event-driven de `auth`.
- [Workflow](../../docs/en/workflow.md)
