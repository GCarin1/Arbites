# Spec Delta — capability: auth

**Operation:** MODIFIED
**Target spec on apply:** `.doctrina/specs/auth/spec.md`

---

O 0100 fechou a porta para anônimos; este delta decide o que cada papel
pode fazer depois de entrar, e dá ao admin um interruptor por superfície
perigosa.

O achado que ordenou o trabalho: a execução de código arbitrário não está
em `POST /runs/local` (que roda um alvo já configurado), e sim em
`PUT /targets` — `python_path` e `working_dir` do payload vão direto para
`create_subprocess_exec` em `backend/arbites/runner.py`. Configurar um alvo
é privilégio de administração; rodar um alvo configurado é trabalho de QA.

```ops
bump-version minor
append-requirement ubiquitous: The system shall atribuir a cada papel um alcance fixo — `viewer` só lê, `editor` lê e escreve os artefatos de QA (requisitos, casos de teste, execuções, defeitos, afazeres, reuniões, decisões, daily) e dispara execuções de alvos já configurados, e `admin` acumula tudo isso mais as superfícies governadas.
append-requirement ubiquitous: The system shall exigir papel `admin` nas superfícies governadas: `PUT /targets` (define o executável e o diretório do subprocess), `GET /automation/browse-features` (navega o filesystem do servidor), `GET|PUT /targets/{name}/env` e `GET /env/catalog` (segredos do projeto-alvo), `PUT /settings/github/token` e as chaves de IA, e `POST /import/xray` e `POST /import/xray/confirm`.
append-requirement ubiquitous: The system shall manter um registro de interruptores administráveis — `local_runner`, `filesystem_browse`, `target_env`, `ai` e `xray_import` — persistido no mesmo banco durável das contas, cada um ligado por padrão para não alterar em silêncio o comportamento da instalação local.
append-requirement ubiquitous: The system shall expor `GET /admin/switches` (estado de todos, legível por qualquer sessão para que a UI esconda o que está desligado) e `PUT /admin/switches/{name}` (apenas `admin`), registrando quem alterou e quando.
append-requirement event: When uma requisição de escrita (qualquer método que não seja GET, HEAD ou OPTIONS) chega de uma sessão com papel `viewer`, the system shall recusá-la com 403 e código `forbidden`, exceto a troca da própria senha e o logout.
append-requirement event: When uma rota governada por um interruptor desligado é chamada, the system shall recusá-la com 403 e código `feature_disabled`, nomeando o interruptor responsável.
append-requirement state: While o papel da sessão não alcança a rota, the system shall responder 403 com código `forbidden` — nunca 404, para não transformar autorização em adivinhação de rota.
append-requirement unwanted: The system shall not permitir que `PUT /targets` seja alcançado por papel diferente de `admin`; um alvo define o binário e o diretório de trabalho de um subprocess, então configurá-lo equivale a executar código no servidor.
append-requirement unwanted: The system shall not deixar um interruptor desligado ser contornado por outra rota que faça a mesma coisa; o interruptor governa a capacidade, não a URL.
append-criterion [verified] Um `viewer` lê tudo por GET e recebe 403 `forbidden` em qualquer escrita, inclusive nas rotas que não existiam quando o papel foi criado — verified by `backend/tests/test_authorization.py`.
append-criterion [verified] Um `editor` cria artefatos e dispara um run local, mas recebe 403 em `PUT /targets`, no navegador de filesystem, no `.env` do alvo, no token do GitHub e no import Xray — verified by `backend/tests/test_authorization.py`.
append-criterion [verified] Desligar `local_runner` faz `POST /runs/local` responder 403 `feature_disabled` citando o interruptor, e religá-lo devolve a rota, sem reiniciar o processo — verified by `backend/tests/test_authorization.py`.
append-criterion [verified] Os interruptores nascem todos ligados, sobrevivem ao reinício do processo e só o `admin` os altera — verified by `backend/tests/test_authorization.py`.
```
