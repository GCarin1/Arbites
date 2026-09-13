# Tasks — Change 0107-keepalive-no-sse-atras-do-tunel

- [x] `api.py`: constante `SSE_KEEPALIVE_SECONDS` e `asyncio.wait_for` no laço do `stream_run`.
- [x] `api.py`: emitir comentário SSE (`: keepalive`) no silêncio, invisível ao `EventSource`.
- [x] `test_local_runs.py`: provar que um run silencioso continua recebendo bytes.
- [x] `docs/self-hosting.md`: avisar que o hostname do dispositivo pode não ser `umbrel.local`.
- [x] `docs/self-hosting.md` §2.4: rota por nome de container na rede do túnel, com o comando que descobre a rede.
- [x] `docs/self-hosting.md` §5: nota sobre SSE atravessar o túnel e o papel do keepalive.
- [x] `docker-compose.yml`: ponteiro para a variante, sem duplicar o comando.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0107-keepalive-no-sse-atras-do-tunel/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
