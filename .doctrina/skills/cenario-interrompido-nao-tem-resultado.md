---
name: cenario-interrompido-nao-tem-resultado
description: Progresso ao vivo deduz o status pela AUSÊNCIA de falha — o que só vale para cenário que chegou ao fim. Ao fechar um parcial depois de matar o processo (timeout/cancelamento), o cenário aberto vira `passed` sem nunca ter terminado. Quem interrompe precisa dizer que interrompeu.
when: Ao escrever ou mexer em parser de progresso ao vivo, fecho de resultado parcial, timeout/cancelamento de subprocess, ou qualquer código que derive "passou" de "não vi erro"; e ao investigar um caso verde que ninguém sabe explicar.
---

# Skill — cenario-interrompido-nao-tem-resultado

## When to use this skill

- Você vai fechar um resultado parcial vindo de um stream (behave, pytest,
  playwright, qualquer runner que imprima conforme anda).
- Você vai matar um subprocess por timeout, cancelamento ou desligamento.
- Alguém relata um caso `passed` que não deveria estar verde.

## O defeito (change 0137)

O parser do stream fecha o cenário anterior quando vê um cenário NOVO:

```python
status = "failed" if run._live_failed else "passed"
```

`_live_failed` é "vi uma linha de passo falhado". A dedução é honesta
**enquanto o cenário termina**: um cenário que rodou até o fim sem falha
passou. Ela deixa de ser honesta no instante em que alguém mata o processo:
aí o cenário aberto também não tem falha registrada — e vira `passed`.

O caminho era este:

1. `_collect` chama o fecho do parcial uma última vez, para não perder o
   último cenário do run. Correto.
2. `_collect` roda TAMBÉM depois do `proc.kill()` do timeout.
3. O cenário que estava dormindo num `Quando` vira `passed`.
4. `_mark_pending(run, "blocked", "timeout")` — que existia justamente para
   isso — não conserta: ele só mexe em resultado **pendente**, e o caso já
   tinha deixado de ser pendente no passo 3.

Resultado: run em `timeout`, caso em `passed`. Numa plataforma de
rastreabilidade de teste é o defeito mais caro que existe — verde falso.

## Procedure

1. **Dê ao fecho um parâmetro de interrupção**, não um palpite:
   ```python
   def _live_conclude(self, run, *, interrupted: bool = False) -> None:
       name = run._live_scenario
       run._live_scenario = None
       if interrupted or not name:
           return   # não terminou => não tem resultado
   ```
2. **Propague de quem sabe**: quem chamou `kill()` é quem sabe que matou.
   `_run_one` → `_collect(..., interrupted=timed_out or cancelled)` → fecho.
3. **Deixe o caso PENDENTE** e que o marcador de pendentes faça o trabalho
   (`blocked` + `error: "timeout"`). Não escreva o `blocked` no fecho: duas
   escritas da mesma verdade divergem na primeira mudança.
4. **Prove a regressão dos dois lados**: o teste novo precisa FALHAR contra
   o código antigo. Reverta o parâmetro, rode, veja o `passed` voltar,
   reponha. Sem isso você não sabe se prendeu o defeito ou o acaso.

## Por que só apareceu agora

O defeito era antigo e estava calado: com a versão anterior do runner
externo, a linha do cenário não chegava ao parser dentro dos 3 s do teste,
então o fecho não tinha o que concluir. O container foi reciclado, a
dependência voltou numa versão que descarrega o stream mais cedo, e o mesmo
código passou a gravar o verde.

**Corolário:** dependência de teste não declarada é gate não reprodutível.
Um teste que passa por causa do buffer de um pacote que ninguém fixou não
está provando o que diz provar.

## Anti-patterns

- Derivar `passed` de `not failed` sem saber se o trabalho terminou.
- Confiar que o "marcar pendentes" conserta depois — ele não vê quem já foi
  marcado.
- Chamar o mesmo fecho no caminho feliz e no caminho de morte sem distinguir
  os dois.
- Declarar o teste corrigido sem vê-lo falhar contra o código antigo.

## Related material

- `backend/arbites/runner.py` — `_live_conclude(interrupted=)`, `_collect`,
  `_run_one`.
- `backend/tests/test_local_runs.py` — `test_cenario_morto_no_meio_nao_vira_passed`.
- `.doctrina/changes/archive/2026-09-13-0137-cenario-interrompido-timeout-cancelamento/`
- Relacionada: [[progresso-ao-vivo-fonte-oficial-reconcilia]].
