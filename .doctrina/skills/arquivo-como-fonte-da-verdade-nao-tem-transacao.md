---
name: arquivo-como-fonte-da-verdade-nao-tem-transacao
description: Com o filesystem como fonte de verdade (ADR 0001) não existe transação: todo trecho carregar-alterar-gravar é crítico, e qualquer suspensão ou disputa no meio dele perde dado em silêncio, normalmente com resposta de sucesso.
when: Ao escrever ou revisar rota que carrega um arquivo de estado (execution.json, perfil, contadores), altera e grava; ao acrescentar `await` numa rota que já fazia isso; ao chamar subprocesso que disputa lock (git); ao investigar "gravei e sumiu".
---

# Skill — arquivo-como-fonte-da-verdade-nao-tem-transacao

## When to use this skill

- Uma rota faz `load(...)` → altera → `save(...)` num arquivo de estado.
- Você vai acrescentar um `await` dentro de uma rota que já grava arquivo.
- O código chama um subprocesso que pega lock do recurso (`git`).
- Sintoma: "a operação respondeu 200/201 e o dado não está lá".

## Os dois bugs (reais, changes 0120 e 0123)

**Suspensão no meio do trecho crítico.** A rota de evidência fazia:

```python
execution = exec_ops.load(ws, exec_id)
content = await file.read()        # ← suspende, e o mundo anda
evidence = exec_ops.add_evidence(..., execution, ...)
_save_and_index(ws, conn, execution)
```

Com upload pequeno nada acontece: o `read` resolve sem suspender de fato.
Com upload acima do limite de memória o arquivo vai para disco, o `read`
suspende de verdade, e dois uploads simultâneos partem do mesmo estado.
Medido com seis de 2 MB: **seis respostas 201, seis arquivos no disco, três
registros no `execution.json`**.

**Disputa de lock tratada como "sem histórico".** O git tem um `index.lock`
por repositório. Doze commits simultâneos gravavam **dois**; os outros dez
falhavam, a exceção era engolida, e onze arquivos ficavam fora do histórico
para sempre.

Nos dois casos o usuário recebeu sucesso e o dado não existe.

## Procedure

1. **Marque o trecho crítico**: da primeira leitura do estado até a
   gravação. Dentro dele não pode haver `await`, `subprocess` que dispute
   lock, nem chamada de rede.
2. **Tire o trabalho para fora**, na ordem certa: leia o upload, resolva a
   IA, faça a chamada externa — e só então carregue, altere e grave. Mover
   uma linha costuma bastar; travar por precaução esconde a próxima
   violação em vez de impedi-la.
3. **Quando o recurso tem lock próprio** (git), serialize com um
   `threading.Lock` de módulo e tire o bloqueio do laço de eventos com
   `asyncio.to_thread` — é o padrão que o projeto já usa para IA e CI.
4. **Falha de registro nunca é silenciosa**: `except` que engole tem de
   deixar `log.warning` dizendo a ação e o arquivo, senão a ausência vira
   mistério.
5. **Prove com concorrência de verdade.** `TestClient` serializa as
   requisições e não reproduz nada:
   ```python
   transport = httpx.ASGITransport(app=app)
   async with httpx.AsyncClient(transport=transport, base_url="http://t",
                                cookies=cookies) as ac:
       await asyncio.gather(*[envia(i) for i in range(6)])
   ```
   Para lock de subprocesso, `threading.Thread` direto no módulo.
6. **Rode o teste novo contra o código ANTIGO** (`git stash`): se ele passa
   sem a correção, ele não está provando a corrida.

## Anti-patterns

- Assumir que rota `async` sem `await` explícito é segura e depois
  acrescentar um `await` no meio dela sem revisar o trecho.
- Testar upload concorrente com arquivo pequeno: não suspende, e o teste
  fica verde por acidente.
- `except Exception: return None` em caminho de persistência.
- Trava global "por garantia" antes de entender onde está a suspensão.

## Related material

- `.doctrina/changes/archive/2026-09-13-0123-upload-simultaneo-evidencia-responde/`
- `.doctrina/changes/archive/2026-09-13-0120-versionamento-serializado-observavel-commit/`
- `backend/tests/test_executions_concurrency.py` — corrida por ASGI.
- `backend/arbites/versioning.py` — `_git_lock` e o `log.warning` do commit perdido.
