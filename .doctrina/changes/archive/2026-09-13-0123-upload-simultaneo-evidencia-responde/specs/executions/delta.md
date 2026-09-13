# Spec Delta — capability: executions

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/executions/spec.md`

---

A rota de evidência carrega a execution, **espera o arquivo chegar** e só
então grava. Entre carregar e gravar existe uma suspensão, e um upload
grande o bastante para ir para disco em vez de ficar em memória a
transforma numa janela de verdade: duas pessoas anexando evidência ao mesmo
ciclo ao mesmo tempo carregam o mesmo estado, e a segunda a gravar apaga o
registro da primeira.

Medido com seis uploads simultâneos de 2 MB: **seis respostas 201, seis
arquivos no disco, três registros no `execution.json`**. É a pior
combinação possível — a pessoa recebe confirmação de que a evidência foi
anexada, o arquivo ocupa espaço, e nem o produto nem a trilha de auditoria
sabem que ele existe. Evidência é justamente o artefato que prova o que foi
testado.

A correção é fechar a janela: ler o arquivo **antes** de carregar a
execution. Não sobra suspensão entre a leitura do estado e a gravação dele,
e o ciclo de leitura-alteração-escrita volta a ser indivisível, como já é
nas demais rotas de resultado.

```ops
bump-version patch
append-requirement unwanted: The system shall not suspender a requisição entre carregar a execution e gravá-la; um upload concorrente que aguarde no meio desse trecho faz a última gravação apagar o registro das anteriores.
append-criterion [unverified] Seis evidências enviadas ao mesmo tempo para o mesmo resultado são todas registradas no `execution.json`, com um arquivo em disco para cada — verified by `backend/tests/test_executions_concurrency.py`.
```
