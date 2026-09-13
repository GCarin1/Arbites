# Spec Delta — capability: local-automation

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/local-automation/spec.md`

---

O stream de log do run nasceu para `localhost`, onde ninguém no meio do
caminho tem opinião sobre conexão parada. Atrás de um proxy — o Cloudflare
Tunnel, aqui — uma conexão ociosa é derrubada, e o `await queue.get()` do
`stream_run` pode ficar minutos sem emitir byte nenhum enquanto um passo do
Behave roda em silêncio.

O sintoma seria o pior tipo: o run continua correndo no servidor, mas o
terminal na tela congela e depois cai, dando a impressão de que a automação
travou. Um comentário SSE periódico resolve — `EventSource` ignora linhas
que começam com `:`, então o keepalive não polui o terminal nem exige
mudança no cliente.

```ops
bump-version minor
append-requirement ubiquitous: The system shall emitir um comentário SSE de keepalive a cada 15 segundos de silêncio no stream do run, para que um proxy no caminho não derrube por ociosidade uma conexão cujo run ainda está vivo.
append-requirement unwanted: The system shall not emitir o keepalive como evento de dados; ele é um comentário SSE (linha iniciada por `:`), invisível ao `EventSource` e ao terminal da UI.
append-criterion [verified] Um run que fica em silêncio além do intervalo de keepalive continua recebendo bytes no stream, e o que chega no período é comentário — nenhuma linha nova aparece no terminal — verified by `backend/tests/test_local_runs.py`.
```
