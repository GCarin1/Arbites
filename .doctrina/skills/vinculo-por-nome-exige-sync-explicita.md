---
name: vinculo-por-nome-exige-sync-explicita
description: Quando dois sistemas se vinculam por um identificador humano (nome de cenário, título, caminho) em vez de um ID estável, o vínculo é frágil por natureza — a mitigação obrigatória é uma sync explícita e re-executável que classifica os estados (novo/modificado/renomeado-quebrado) e deixa o usuário decidir o que fazer.
when: O agente está desenhando ou revisando um vínculo entre artefatos de sistemas diferentes onde não há ID compartilhado estável (ex.: cenário de .feature ↔ CT do Arbites por nome, quando escrever a tag no repo externo é proibido).
---

# Skill — vinculo-por-nome-exige-sync-explicita

## When to use this skill

- O agente precisa vincular artefatos de um repositório externo read-only
  (não pode gravar um ID/tag lá) a artefatos internos.
- O agente está revisando um vínculo existente baseado em nome/título/path
  e avaliando os modos de falha.

## Procedure

1. **Prefira ID estável quando puder gravar dos dois lados.** Vínculo por
   nome é a opção quando um dos lados é read-only (aqui: ADR 0003 — o
   Arbites nunca escreve no repositório de automação; decisão do usuário
   na change 0075 de preservar isso).
2. **Assuma que o vínculo VAI quebrar** (rename, remoção, refactor) e
   desenhe a detecção desde o início: uma sync re-executável que compara o
   estado externo atual com os vínculos internos e classifica cada item:
   - **novo** (existe lá, sem vínculo aqui),
   - **modificado** (vínculo ok, conteúdo divergiu — diff de steps/corpo),
   - **quebrado** (vínculo aponta para nome que não existe mais).
3. **Nunca resolva silenciosamente.** A sync REPORTA e o usuário decide no
   modal: criar / atualizar / re-vincular / ignorar. Auto-fix de vínculo
   por similaridade é sugestão, nunca ação automática.
4. **Guarde o suficiente para o diff**: o conteúdo importado (steps
   verbatim no body do CT) é a baseline — comparar contra o estado atual
   do arquivo externo detecta "modificado" sem tabela extra.

## Anti-patterns

- Vincular por nome e não oferecer sync — o vínculo quebra no primeiro
  rename e ninguém percebe (resultados param de casar silenciosamente).
- Re-vincular automaticamente pelo "nome mais parecido" — um rename +
  cenário novo com nome similar vira vínculo errado.
- Guardar hash/snapshot paralelo quando o próprio corpo do artefato
  interno já serve de baseline para o diff.

## Related material

- `.doctrina/changes/0075-lastreamento-feature-ct-por-nome-de-cenario/`
- ADR 0003 (vínculo por tag; repositório de automação read-only).
- [[fonte-do-preview-diverge-da-fonte-da-operacao]] — prima: divergência
  entre estados que o usuário vê.
