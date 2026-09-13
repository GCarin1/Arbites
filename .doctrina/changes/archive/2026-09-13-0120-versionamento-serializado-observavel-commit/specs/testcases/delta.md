# Spec Delta — capability: testcases

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/testcases/spec.md`

---

A change 0112 acertou a regra — "registro nunca derruba escrita" — e errou o
que fazer quando o registro falha: qualquer erro do git é engolido e o commit
simplesmente não acontece, sem sinal nenhum.

Medido: doze commits disparados ao mesmo tempo gravam **dois**. Os outros dez
morrem na disputa pelo `index.lock` do git, e onze arquivos ficam fora do
histórico para sempre — nenhuma ação futura os recolhe, porque o histórico
daquele arquivo já "existe". A instância é de time; duas pessoas salvando ao
mesmo tempo é o caso normal, não o excepcional.

Duas correções, do mesmo defeito:

- **Serializar.** O git tem um lock por repositório, então duas escritas
  simultâneas competem por ele. Uma fila no processo transforma a disputa em
  espera, que é o que ela deveria ter sido desde o início.
- **Registrar a falha.** Continuar sem derrubar a escrita está certo; fazê-lo
  em silêncio absoluto não. Um commit que não aconteceu vira log de aviso,
  para que a ausência no histórico seja explicável em vez de misteriosa.

E, já que a fila existe, o subprocesso sai do event loop: o `asyncio.to_thread`
é o padrão que a casa já usa para trabalho bloqueante (IA, CI), e segurar o
loop a cada gravação de caso de teste penaliza toda requisição em curso.

```ops
bump-version minor
append-requirement ubiquitous: The system shall serializar as operações de git do workspace numa fila única por processo, para que duas escritas simultâneas esperem em vez de disputar o lock do repositório.
append-requirement ubiquitous: The system shall executar as operações de git fora do laço de eventos, como já faz com as demais chamadas bloqueantes.
append-requirement event: When um commit de versionamento não acontece por falha do git, the system shall registrar um aviso no log identificando a ação e o motivo, em vez de seguir em silêncio.
append-criterion [unverified] Doze gravações simultâneas geram doze commits e não deixam nenhum arquivo fora do histórico — verified by `backend/tests/test_versioning.py`.
append-criterion [unverified] Um commit impedido por falha do git deixa aviso no log com a ação que se perdeu, e a operação do usuário continua respondendo normalmente — verified by `backend/tests/test_versioning.py`.
```
