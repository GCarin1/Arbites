# Tasks — Change 0101-endurecimento-das-rotas-perigosas

- [x] `auth.py`: tabela `switches` no banco durável, registro dos interruptores conhecidos, leitura e escrita com autor e data.
- [x] `api.py`: helper `require_role` com 403 `forbidden` (nunca 404).
- [x] `api.py`: recusa genérica de escrita para `viewer` no gate de sessão — cobre rota futura sem precisar lembrar de anotá-la.
- [x] `api.py`: helper `require_switch` com 403 `feature_disabled` nomeando o interruptor.
- [x] `api.py`: exigir `admin` em `PUT /targets` (o RCE real), browse-features, `.env` do alvo, token do GitHub, chaves de IA e import Xray.
- [x] `api.py`: ligar os interruptores `local_runner`, `filesystem_browse`, `target_env`, `ai` e `xray_import` às rotas correspondentes.
- [x] `api.py`: `GET /admin/switches` e `PUT /admin/switches/{name}`.
- [x] `frontend`: expor papel e interruptores ao App e esconder o que não se alcança.
- [x] `backend/tests/test_authorization.py` cobrindo os 4 critérios, com varredura automática das rotas de escrita para o caso do `viewer`.

## Closing steps

- [x] Apply the change: merge each delta into the corresponding spec.
- [x] Archive the change folder to `.doctrina/changes/archive/2026-09-12-0101-endurecimento-das-rotas-perigosas/`.
- [x] Update `.doctrina/index.json` with new or modified artifacts.
