---
name: progresso-ao-vivo-fonte-oficial-reconcilia
description: Progresso em tempo real parseado de um stream de texto é sempre best-effort — pode e deve existir para UX, mas a fonte oficial estruturada (JSON/artefato final) SEMPRE reconcilia o estado no fim; o live nunca é a verdade final.
when: O agente vai mostrar progresso ao vivo de um processo externo (runner de testes, build, pipeline) parseando stdout/log, quando o resultado estruturado confiável só existe ao final.
---

# Skill — progresso-ao-vivo-fonte-oficial-reconcilia

## When to use this skill

- O agente vai atualizar UI/estado durante a execução de um subprocess cuja
  saída estruturada (JSON, XML) só é escrita ao final.
- O agente está revisando um parser de stream de log que alimenta estado
  persistido.

## Procedure

1. **Duas camadas, papéis claros.** Camada live: parse do stream
   (best-effort, marcada como parcial). Camada oficial: o artefato
   estruturado do fim do processo. A oficial SEMPRE sobrescreve a live —
   mesmo que pareçam iguais, reconcilie incondicionalmente.
2. **Parse defensivo do stream**: regexes tolerantes, keywords em todos os
   idiomas que o processo emite (behave: EN e PT — "Scenario:"/"Cenário:",
   "passed"/"failed" aparecem em ambos), e falha de parse = ignorar a
   linha, nunca crashar o runner.
3. **Persistência com parcimônia**: gravar a cada step gera IO/lock demais;
   persistir por unidade concluída (cenário) equilibra vivacidade e custo.
   O status parcial fica visualmente distinto de final (ex.: run ainda
   `running`).
4. **Nunca derive decisões da camada live** (métricas, alertas, gates):
   tudo que importa lê o estado reconciliado.

## Anti-patterns

- Confiar no parse do stream como estado final (formato do log muda numa
  versão nova do runner e os resultados "mudam" silenciosamente).
- Pular a reconciliação quando "o live já bateu" — divergências raras são
  exatamente as que importam.
- Persistir a cada linha/step — colisão de locks com o watcher (ver
  [[watcher-vs-handler-mesma-rajada-database-locked]]).

## Related material

- `.doctrina/changes/0076-execucao-rastreada-ao-vivo-rodar-1-n-feature/`
- `backend/arbites/runner.py` (`_collect` = reconciliação oficial via
  Cucumber JSON) · `backend/arbites/behave_json.py`.
