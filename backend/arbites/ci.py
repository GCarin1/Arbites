"""GitHub Actions (M4) — dispatch, correlação, polling e coleta por artifact.

Restrição real da API (ADR 0006): logs completos de job só após o término;
ao vivo existe apenas o status de workflow/jobs/steps do workflow. Por
isso a coleta é por artifact (Cucumber JSON), parseado pelo MESMO adapter
do run local (`behave_json`) — executions idênticas nos dois caminhos.

Token: PAT fine-grained via keyring (ADR 0008) — nunca em YAML, nunca no
índice, nunca logado.
"""

from __future__ import annotations

import io
import os
import sqlite3
import time
import zipfile
from datetime import datetime, timezone
from typing import Any, Protocol

from . import executions as exec_ops
from . import tls as tls_ops
from .behave_json import BehaveJsonError, parse_behave_json
from .indexer import clear_needs_rerun, reindex_file
from .workspace import Workspace

KEYRING_SERVICE = "arbites-github"
KEYRING_USER = "pat"
CORRELATION_WINDOW_S = 30
POLL_INTERVAL_S = 10


class CIError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ---------------------------------------------------------------------------
# Token (keyring do SO)


# Fora do keyring, só UM lugar: a variável de ambiente do processo (change
# 0160). A ADR 0008 rejeitou "token em arquivo de config" porque o workspace é
# versionável e compartilhável — e continua rejeitando. Ambiente do container
# não é isso: não viaja com o workspace, não entra no git, e é o mesmo canal
# por onde a senha de bootstrap do admin já chega no `docker-compose.yml`.
ENV_TOKEN = "ARBITES_GITHUB_TOKEN"


class TokenStore:
    """O cofre do SO, com uma saída para onde ele não existe.

    Num container não há keychain nenhum, e `keyring` levanta `NoKeyringError`
    na primeira chamada. Antes da change 0160 isso derrubava a aplicação
    INTEIRA com 500 — porque a tela Problemas pergunta pelo estado da
    credencial em todo carregamento, e a pergunta explodia. Ausência de cofre
    é uma resposta legítima ("não há credencial"), não um acidente.
    """

    def set(self, token: str) -> None:
        import keyring

        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)
        except Exception as e:  # noqa: BLE001 — qualquer falha do cofre
            raise CIError(
                "no_keyring",
                "esta instância não tem cofre do sistema operacional (típico"
                f" de container): guardar o token aqui falharia em silêncio."
                f" Defina {ENV_TOKEN} no ambiente do processo — no"
                " docker-compose.yml, do mesmo jeito que a senha de bootstrap"
                f" do admin. Motivo do cofre: {e}",
                409,
            ) from e

    def get(self) -> str | None:
        """O ambiente PRIMEIRO: quem definiu a variável quis aquele token, e
        um resto esquecido no cofre não pode ganhar dele em silêncio."""
        do_ambiente = (os.environ.get(ENV_TOKEN) or "").strip()
        if do_ambiente:
            return do_ambiente
        import keyring

        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:  # noqa: BLE001 — sem cofre é "não há credencial"
            return None

    def available(self) -> bool:
        """Se dá para GUARDAR um token nesta instância. Ler funciona sempre
        (pelo ambiente); guardar, não — e a tela precisa dizer isso antes de
        alguém digitar um token num campo que vai recusar."""
        import keyring

        try:
            keyring.get_keyring().get_password(KEYRING_SERVICE, "__probe__")
        except Exception:  # noqa: BLE001
            return False
        return True

    def source(self) -> str | None:
        if (os.environ.get(ENV_TOKEN) or "").strip():
            return "env"
        return "keyring" if self.get() else None

    def status(self) -> dict[str, Any]:
        return {"configured": self.get() is not None}  # nunca o valor


# ---------------------------------------------------------------------------
# Cliente GitHub — interface fina, 1 método ≈ 1 endpoint REST


class GitHubClient(Protocol):
    def dispatch_workflow(self, repo: str, workflow: str, ref: str,
                          inputs: dict[str, str]) -> None: ...
    def list_recent_dispatch_runs(self, repo: str, workflow: str) -> list[dict]: ...
    def list_workflow_runs(self, repo: str, workflow: str | None,
                           page: int, per_page: int,
                           created: str | None = ...) -> list[dict]: ...
    def get_run(self, repo: str, run_id: int) -> dict: ...
    def get_jobs(self, repo: str, run_id: int) -> list[dict]: ...
    def list_artifacts(self, repo: str, run_id: int) -> list[dict]: ...
    def download_artifact(self, repo: str, artifact_id: int) -> bytes: ...


class HttpxGitHub:
    """Implementação real (httpx) com backoff em rate limit."""

    def __init__(self, tokens: TokenStore, credential=None):
        self.tokens = tokens
        # Estado da credencial (change 0157). Opcional para não quebrar quem
        # constrói o cliente sem workspace — sem ele o comportamento é o de
        # antes, só sem memória da recusa.
        self.credential = credential

    def _request(self, method: str, path: str, **kwargs) -> Any:
        import httpx

        token = self.tokens.get()
        if not token:
            raise CIError("no_token", "PAT do GitHub não configurado", 409)
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        for attempt in range(4):
            try:
                resp = httpx.request(
                    method, f"https://api.github.com{path}",
                    headers=headers, timeout=30,
                    # Rede corporativa re-assina o TLS com uma CA própria; sem
                    # apontar o bundle, toda chamada morre em
                    # CERTIFICATE_VERIFY_FAILED (change 0183).
                    verify=tls_ops.verify(), **kwargs,
                )
            except httpx.TransportError as exc:
                # Sem isto o erro subia cru e virava 500 com traceback: quem
                # clicou em "Buscar execuções" via uma parede de stack trace
                # em vez do que fazer. A ingestão é retomável (a marca d'água
                # é o disco), então recusar limpo não perde nada.
                raise self._sem_alcance(exc) from exc
            # 401 é credencial, sempre — e repetir uma credencial ruim só
            # gasta tempo e chega ao mesmo lugar (change 0157).
            if resp.status_code == 401:
                raise self._recusa(401, resp.text)
            # 403 é ambíguo no GitHub: é rate limit quando a cota zerou, e é
            # permissão quando o token não alcança o recurso. Tratar os dois
            # como rate limit faria a ferramenta tentar de novo para sempre
            # contra um token revogado, em silêncio — que é o defeito que
            # esta change existe para matar.
            if resp.status_code == 403 and not _e_rate_limit(resp):
                raise self._recusa(403, resp.text)
            if resp.status_code in (403, 429) and attempt < 3:
                time.sleep(2 ** attempt)  # backoff em rate limit (spec)
                continue
            if resp.status_code >= 400:
                raise CIError("github_error",
                              f"GitHub {resp.status_code}: {resp.text[:200]}")
            if self.credential is not None:
                self.credential.registrar_sucesso()
            return resp
        raise CIError("rate_limited", "rate limit persistente na API do GitHub")

    def _sem_alcance(self, exc: Exception) -> CIError:
        """Falha de transporte vira recusa explicada.

        Certificado e rede pedem ações opostas — configurar um bundle e
        esperar — então não podem sair com a mesma mensagem.
        """
        if tls_ops.e_erro_de_certificado(exc):
            return CIError("tls_untrusted",
                           tls_ops.explicacao("api.github.com"), status=502)
        return CIError(
            "unreachable",
            f"não foi possível falar com api.github.com: {exc}."
            " Verifique a conexão e o proxy da rede.",
            status=502,
        )

    def _recusa(self, status: int, corpo: str) -> CIError:
        mensagem = _motivo(corpo)
        if self.credential is not None:
            self.credential.registrar_recusa(status, mensagem)
        return CIError(
            "bad_credential",
            f"o GitHub recusou a credencial (HTTP {status}): {mensagem}",
            status=409,
        )

    def dispatch_workflow(self, repo, workflow, ref, inputs):
        self._request(
            "POST", f"/repos/{repo}/actions/workflows/{workflow}/dispatches",
            json={"ref": ref, "inputs": inputs},
        )

    def list_recent_dispatch_runs(self, repo, workflow):
        resp = self._request(
            "GET",
            f"/repos/{repo}/actions/workflows/{workflow}/runs"
            "?event=workflow_dispatch&per_page=10",
        )
        return resp.json().get("workflow_runs", [])

    def list_workflow_runs(self, repo, workflow=None, page=1, per_page=50,
                           created=None):
        """Runs CONCLUÍDOS do repositório, do mais novo para o mais velho.

        Diferente de `list_recent_dispatch_runs`, aqui NÃO se filtra por
        `event=workflow_dispatch`: o run que interessa à observabilidade é
        justamente o que ninguém daqui disparou — o `schedule` que roda de
        madrugada. Paginado porque voltar depois de uma semana fora tem de
        trazer a semana inteira, não a primeira página dela.
        """
        alvo = (
            f"/repos/{repo}/actions/workflows/{workflow}/runs"
            if workflow else f"/repos/{repo}/actions/runs"
        )
        consulta = f"status=completed&per_page={per_page}&page={page}"
        if created:
            # O provedor filtra por data no servidor (change 0190). Sem isto,
            # alcançar uma lacuna antiga custa paginar por tudo que veio
            # depois dela — trabalho que já foi feito uma vez.
            from urllib.parse import quote

            consulta += f"&created={quote(created, safe='')}"
        resp = self._request("GET", f"{alvo}?{consulta}")
        return resp.json().get("workflow_runs", [])

    def get_run(self, repo, run_id):
        return self._request("GET", f"/repos/{repo}/actions/runs/{run_id}").json()

    def get_jobs(self, repo, run_id):
        resp = self._request("GET", f"/repos/{repo}/actions/runs/{run_id}/jobs")
        return resp.json().get("jobs", [])

    def list_artifacts(self, repo, run_id):
        resp = self._request("GET", f"/repos/{repo}/actions/runs/{run_id}/artifacts")
        return resp.json().get("artifacts", [])

    def download_artifact(self, repo, artifact_id):
        return self._request(
            "GET", f"/repos/{repo}/actions/artifacts/{artifact_id}/zip",
            follow_redirects=True,
        ).content


# ---------------------------------------------------------------------------
# Orquestração


def _e_rate_limit(resp) -> bool:
    """403 com cota zerada é limite de taxa; 403 sem cota zerada é permissão.

    O cabeçalho é a evidência: o GitHub zera `x-ratelimit-remaining` quando
    barra por cota. O texto do corpo é o segundo sinal, para o caso do
    cabeçalho não vir (proxy corporativo costuma podar cabeçalho).
    """
    if resp.headers.get("x-ratelimit-remaining") == "0":
        return True
    if resp.headers.get("retry-after"):
        return True
    corpo = (resp.text or "").lower()
    return "rate limit" in corpo or "secondary rate" in corpo or "abuse" in corpo


def _motivo(corpo: str) -> str:
    """Extrai a frase do provedor. Repassar o motivo dele é melhor do que
    inventar um nosso: 'Bad credentials' e 'Resource not accessible by
    personal access token' pedem ações diferentes de quem lê."""
    try:
        import json as _json

        dados = _json.loads(corpo or "{}")
        if isinstance(dados, dict) and dados.get("message"):
            return str(dados["message"])[:200]
    except ValueError:
        pass
    return (corpo or "sem detalhe").strip()[:200]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CIManager:
    def __init__(self, ws: Workspace, conn: sqlite3.Connection,
                 client: GitHubClient, tokens: TokenStore):
        self.ws = ws
        self.conn = conn
        self.client = client
        self.tokens = tokens

    def _target(self, name: str) -> dict:
        for target in self.ws.config().get("automation_targets") or []:
            if target.get("name") == name:
                github = target.get("github") or {}
                if not github.get("repo") or not github.get("workflow"):
                    # A mensagem antiga nomeava o bloco do YAML, que não tinha
                    # campo na tela: quem levava o 422 não tinha onde mexer
                    # (change 0172).
                    raise CIError(
                        "no_github",
                        f"o alvo '{name}' não tem repositório e workflow do"
                        " GitHub configurados, então não há para onde disparar."
                        " Preencha os dois em Automação → Configurar; sem eles"
                        " só a execução local funciona.",
                        422,
                    )
                return target
        raise CIError("not_found", f"target '{name}' não configurado", 404)

    def dispatch(self, target_name: str, ref: str | None,
                 inputs: dict[str, str], testcases: list[dict]) -> dict:
        """Dispara o workflow e cria a execution github_actions correlacionada."""
        target = self._target(target_name)
        github = target["github"]
        repo, workflow = github["repo"], github["workflow"]
        ref = ref or github.get("ref", "main")

        dispatched_at = datetime.now(timezone.utc)
        self.client.dispatch_workflow(repo, workflow, ref, inputs)

        # a API não retorna o run id do dispatch: correlaciona pelo run mais
        # recente do workflow criado após o dispatch (janela de 30 s)
        run = None
        deadline = time.time() + CORRELATION_WINDOW_S
        while time.time() < deadline:
            for candidate in self.client.list_recent_dispatch_runs(repo, workflow):
                created = candidate.get("created_at", "")
                if created >= dispatched_at.strftime("%Y-%m-%dT%H:%M:%SZ"):
                    run = candidate
                    break
            if run:
                break
            time.sleep(1)
        if not run:
            raise CIError("correlation_failed",
                          "nenhum run do workflow apareceu na janela de 30 s")

        execution = exec_ops.create(
            self.ws,
            name=f"CI {target_name} run {run['id']}",
            owner="github-actions",
            sprint=None,
            environment=target_name,
            testcases=testcases,
            origin="github_actions",
        )
        execution["ci"] = {
            "workflow_run_id": run["id"],
            "run_url": run.get("html_url"),
            "commit_sha": run.get("head_sha"),
            "artifact_id": None,
            "repo": repo,
            "artifact_name": github.get("artifact_name", "cucumber-report"),
        }
        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)
        return execution

    def status(self, exec_id: str) -> dict:
        """Status consolidado: workflow + jobs + steps (do workflow, não Gherkin)."""
        execution = exec_ops.load(self.ws, exec_id)
        ci = execution.get("ci") or {}
        if not ci.get("workflow_run_id"):
            raise CIError("not_ci", f"{exec_id} não é uma execution de CI", 422)
        run = self.client.get_run(ci["repo"], ci["workflow_run_id"])
        jobs = self.client.get_jobs(ci["repo"], ci["workflow_run_id"])
        return {
            "execution_id": exec_id,
            "workflow": {
                "id": run.get("id"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "html_url": run.get("html_url"),
            },
            "jobs": [
                {
                    "name": job.get("name"),
                    "status": job.get("status"),
                    "conclusion": job.get("conclusion"),
                    "steps": [
                        {
                            "name": step.get("name"),
                            "status": step.get("status"),
                            "conclusion": step.get("conclusion"),
                        }
                        for step in job.get("steps", [])
                    ],
                }
                for job in jobs
            ],
            "poll_interval_seconds": POLL_INTERVAL_S,
        }

    def collect(self, exec_id: str) -> dict:
        """Baixa o artifact, parseia o Cucumber JSON e popula a execution."""
        execution = exec_ops.load(self.ws, exec_id)
        ci = execution.get("ci") or {}
        run = self.client.get_run(ci["repo"], ci["workflow_run_id"])
        if run.get("status") != "completed":
            raise CIError("not_completed",
                          f"workflow ainda {run.get('status')}", 409)

        artifacts = self.client.list_artifacts(ci["repo"], ci["workflow_run_id"])
        wanted = ci.get("artifact_name", "cucumber-report")
        artifact = next((a for a in artifacts if a.get("name") == wanted), None)
        if not artifact:
            raise CIError("artifact_missing",
                          f"artifact '{wanted}' não encontrado no run", 404)
        blob = self.client.download_artifact(ci["repo"], artifact["id"])
        execution["ci"]["artifact_id"] = artifact["id"]

        results_found = 0
        recorded: set[str] = set()  # CTs com resultado novo (0090)
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            json_names = [n for n in zf.namelist() if n.endswith(".json")]
            if not json_names:
                raise CIError("artifact_invalid", "artifact sem Cucumber JSON", 422)
            merged: dict = {}
            for name in json_names:
                try:
                    merged.update(
                        parse_behave_json(
                            zf.read(name), self.ws.id_prefixes()["testcase"]
                        )
                    )
                except BehaveJsonError:
                    continue
            if not merged:
                raise CIError("artifact_invalid",
                              "nenhum Cucumber JSON parseável no artifact", 422)
            for ct_id, scenario in merged.items():
                try:
                    result = exec_ops.set_result_status(
                        execution, ct_id, scenario.status, "github-actions",
                        comment=scenario.scenario_name,
                    )
                except exec_ops.ExecutionError:
                    continue
                result["steps"] = scenario.steps
                result["duration_seconds"] = scenario.duration_seconds
                result["error"] = scenario.error
                results_found += 1
                recorded.add(ct_id)
            # screenshots publicados no artifact sob evidences/CT-XXXX/
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) >= 3 and parts[0] == "evidences" and not name.endswith("/"):
                    ct_id = parts[1]
                    try:
                        exec_ops.add_evidence(
                            self.ws, execution, ct_id, parts[-1], zf.read(name),
                            None, "artifact do GitHub Actions", "github-actions",
                        )
                    except exec_ops.ExecutionError:
                        continue

        path = exec_ops.save(self.ws, execution)
        reindex_file(self.ws, self.conn, path)
        for ct_id in recorded:
            clear_needs_rerun(self.ws, self.conn, ct_id)  # 0090
        return {"execution": execution, "results_collected": results_found}
