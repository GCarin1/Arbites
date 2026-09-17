"""Ingestão de runs que o Arbites NÃO disparou (changes 0153/0154, ADR 0016).

O que estes testes provam, em uma frase: o cron que nasce no GitHub aparece
aqui sozinho, repetir a ingestão não duplica, ficar dias fora não perde
nada, e sinal desconhecido entra sem mudar código.

O fake do GitHub é de propósito burro — um dicionário de runs e de zips. O
que está sob teste é a orquestração (marca d'água, paginação, idempotência,
recuo), não o cliente HTTP, que é uma casca de 1 método ≈ 1 endpoint.
"""

import io
import json
import zipfile

import pytest
import yaml
from conftest import login_admin
from fastapi.testclient import TestClient

from arbites.api import create_app
from arbites.ci import CIError, TokenStore
from arbites.ci_ingest import MANIFESTO


def _zip(arquivos: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for nome, bruto in arquivos.items():
            zf.writestr(nome, bruto)
    return buffer.getvalue()


def manifesto(sinais: list[dict], anexos: list[dict] | None = None) -> bytes:
    return json.dumps({
        "version": 1, "signals": sinais, "attachments": anexos or [],
    }).encode("utf-8")


def _ha_dias(dias: float) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc)
            - timedelta(days=dias)).isoformat().replace("+00:00", "Z")


class FakeGitHub:
    """Runs e artifacts em memória, do mais novo para o mais velho."""

    def __init__(self):
        self.runs: list[dict] = []
        self.artifacts: dict[int, bytes] = {}
        self.chamadas_de_download = 0
        self.listagens: list[str | None] = []  # o `created` de cada listagem
        self.falhar_em: set[int] = set()  # run_ids que respondem com erro
        self.erro: CIError | None = None  # qual erro (padrão: limite de taxa)

    def adicionar(self, run_id: int, *, event="schedule", conclusion="success",
                  artifact: bytes | None = None, started=None):
        # Data relativa a AGORA por padrão: a busca passou a ter janela
        # (change 0190), e datas fixas tornariam a suíte dependente do
        # relógio — passando hoje e falhando daqui a um mês.
        started = started or _ha_dias(1)
        self.runs.insert(0, {
            "id": run_id, "name": "qa-nightly", "event": event,
            "conclusion": conclusion, "head_sha": f"sha{run_id}",
            "head_branch": "main", "run_started_at": started,
            "updated_at": started, "html_url": f"https://gh/run/{run_id}",
        })
        if artifact is not None:
            self.artifacts[run_id] = artifact

    # -- superfície consumida pelo ingestor --------------------------------

    def list_workflow_runs(self, repo, workflow=None, page=1, per_page=50,
                           created=None):
        # O fake HONRA o filtro de data do provedor: sem isso o teste de
        # busca incremental provaria uma coisa e a produção faria outra.
        self.listagens.append(created)
        runs = self.runs
        if created and ".." in created:
            ini, fim = created.split("..", 1)
            runs = [r for r in runs
                    if ini <= (r.get("run_started_at") or "")[:10] <= fim]
        inicio = (page - 1) * per_page
        return runs[inicio:inicio + per_page]

    def list_artifacts(self, repo, run_id):
        if run_id in self.falhar_em:
            raise self.erro or CIError("rate_limited", "limite de taxa persistente")
        if run_id not in self.artifacts:
            return []
        return [{"id": run_id, "name": "observabilidade", "expired": False}]

    def download_artifact(self, repo, artifact_id):
        self.chamadas_de_download += 1
        return self.artifacts[artifact_id]

    # não usados aqui, mas o CIManager exige a forma completa do protocolo
    def dispatch_workflow(self, *a, **k): raise AssertionError("não deve disparar")
    def list_recent_dispatch_runs(self, *a, **k): return []
    def get_run(self, repo, run_id): return {}
    def get_jobs(self, repo, run_id):
        return [{"name": "testes-e2e", "conclusion": "success",
                 "started_at": "2026-09-10T03:00:00Z",
                 "completed_at": "2026-09-10T03:12:00Z",
                 "html_url": f"https://gh/run/{run_id}/job/1"}]


class FakeTokenStore(TokenStore):
    def set(self, token): self._t = token
    def get(self): return "fake-pat"
    def status(self): return {"configured": True}


@pytest.fixture()
def rig(ws):
    fake = FakeGitHub()
    config = ws.config()
    config["observability"] = {
        "sources": [{"provider": "github", "repo": "org/app",
                     "workflow": "qa-nightly.yml"}],
        "max_runs_per_poll": 50,
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8",
    )
    app = create_app(ws.root, watch=False,
                     github_client=fake, token_store=FakeTokenStore())
    with TestClient(app) as client:
        login_admin(client)
        client.fake = fake
        client.ws = ws
        yield client


# -- 0153: o run que ninguém daqui disparou ---------------------------------


def test_run_de_cron_aparece_sem_ninguem_ter_disparado(rig):
    """O caso que motivou a change: `schedule` às 3 da manhã, máquina do QA
    desligada, e mesmo assim o run está lá quando ele liga."""
    rig.fake.adicionar(101, event="schedule", artifact=_zip({
        MANIFESTO: manifesto([{"kind": "test", "name": "cenarios_falhos",
                               "value": 2, "unit": "count"}]),
    }))

    resposta = rig.post("/api/v1/ci/ingest")
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["ingested"] == ["github-101"]

    runs = rig.get("/api/v1/ci/runs").json()["runs"]
    assert [r["run_id"] for r in runs] == ["101"]
    assert runs[0]["event"] == "schedule"
    # e virou ARQUIVO, não só linha no índice (ADR 0001)
    assert (rig.ws.root / "ci" / "2026" / "github-101.md").exists()


def test_ingerir_duas_vezes_nao_duplica(rig):
    rig.fake.adicionar(101, artifact=_zip({MANIFESTO: manifesto([])}))

    primeira = rig.post("/api/v1/ci/ingest").json()
    segunda = rig.post("/api/v1/ci/ingest").json()

    assert primeira["ingested"] == ["github-101"]
    assert segunda["ingested"] == []  # a marca d'água é o disco
    assert rig.fake.chamadas_de_download == 1
    assert len(rig.get("/api/v1/ci/runs").json()["runs"]) == 1


def test_retomada_traz_o_intervalo_inteiro_nao_so_o_ultimo(rig):
    """Três runs aconteceram com a ingestão parada. Religar tem de trazer os
    três — um dashboard que pula dois runs mente sobre a tendência."""
    rig.fake.adicionar(101, artifact=_zip({MANIFESTO: manifesto([])}))
    rig.post("/api/v1/ci/ingest")

    for run_id in (102, 103, 104):
        rig.fake.adicionar(run_id, artifact=_zip({MANIFESTO: manifesto([])}))

    resultado = rig.post("/api/v1/ci/ingest").json()
    assert sorted(resultado["ingested"]) == ["github-102", "github-103", "github-104"]


def test_retomada_atravessa_pagina_ja_conhecida(rig):
    """O intervalo perdido pode estar depois da primeira página. Parar na
    primeira página conhecida perderia justamente o buraco do meio."""
    for run_id in range(1, 130):
        rig.fake.adicionar(run_id, artifact=_zip({MANIFESTO: manifesto([])}))

    resultado = rig.post("/api/v1/ci/ingest?limit=200").json()
    assert len(resultado["ingested"]) == 129


def test_limite_de_taxa_para_sem_perder_run(rig):
    """Quando o GitHub barra, a ingestão para — e a próxima chamada recomeça
    exatamente de onde parou, porque quem responde 'o que falta' é o disco."""
    rig.fake.adicionar(101, artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.adicionar(102, artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.falhar_em = {102}

    parcial = rig.post("/api/v1/ci/ingest").json()
    assert parcial["ingested"] == ["github-101"]
    assert parcial["stopped"] == "rate_limited"

    rig.fake.falhar_em = set()
    retomada = rig.post("/api/v1/ci/ingest").json()
    assert retomada["ingested"] == ["github-102"]


def test_sem_fonte_configurada_recusa_em_vez_de_inventar(ws):
    app = create_app(ws.root, watch=False,
                     github_client=FakeGitHub(), token_store=FakeTokenStore())
    with TestClient(app) as client:
        login_admin(client)
        resposta = client.post("/api/v1/ci/ingest")
        assert resposta.status_code == 409
        assert resposta.json()["error"]["code"] == "no_sources"


# -- 0154: sinal genérico e manifesto ---------------------------------------


def test_sinal_consultavel_por_nome_e_periodo(rig):
    rig.fake.adicionar(101, started="2026-09-08T03:00:00Z", artifact=_zip({
        MANIFESTO: manifesto([{"kind": "perf", "name": "lcp_ms",
                               "value": 2400, "unit": "ms"}]),
    }))
    rig.fake.adicionar(102, started="2026-09-09T03:00:00Z", artifact=_zip({
        MANIFESTO: manifesto([{"kind": "perf", "name": "lcp_ms",
                               "value": 3100, "unit": "ms"}]),
    }))
    rig.post("/api/v1/ci/ingest")

    serie = rig.get("/api/v1/ci/signals/lcp_ms").json()
    assert [p["value"] for p in serie["points"]] == [2400.0, 3100.0]
    assert serie["points"][0]["unit"] == "ms"

    recorte = rig.get("/api/v1/ci/signals/lcp_ms?since=2026-09-09").json()
    assert recorte["count"] == 1


def test_sinal_nunca_visto_entra_sem_mudanca_de_codigo(rig):
    """O Arbites não tem lista de sinais conhecidos. Se o pipeline passar a
    emitir 'violacoes_axe' amanhã, ele entra hoje."""
    rig.fake.adicionar(101, artifact=_zip({
        MANIFESTO: manifesto([
            {"kind": "a11y", "name": "violacoes_axe", "value": 7},
            {"kind": "inventado", "name": "coisa_que_nao_existe", "value": 1.5,
             "unit": "gizmos"},
        ]),
    }))
    rig.post("/api/v1/ci/ingest")

    nomes = {s["name"] for s in rig.get("/api/v1/ci/signals").json()["signals"]}
    assert {"violacoes_axe", "coisa_que_nao_existe"} <= nomes


def test_print_log_e_analise_chegam_como_anexo_hasheado(rig):
    corpo = "# Análise\n\nO tempo de carga subiu 30% nesta semana.\n"
    rig.fake.adicionar(101, artifact=_zip({
        MANIFESTO: manifesto(
            [{"kind": "test", "name": "falhas", "value": 0}],
            [{"kind": "analysis", "path": "analysis.md"},
             {"kind": "screenshot", "path": "shots/home.png"},
             {"kind": "log", "path": "run.log"}],
        ),
        "analysis.md": corpo.encode("utf-8"),
        "shots/home.png": b"\x89PNG\r\n\x1a\nfake",
        "run.log": b"linha 1\nlinha 2\n",
    }))
    rig.post("/api/v1/ci/ingest")

    run = rig.get("/api/v1/ci/runs").json()["runs"][0]
    tipos = {a["kind"] for a in run["attachments"]}
    assert tipos == {"analysis", "screenshot", "log"}
    for anexo in run["attachments"]:
        assert len(anexo["sha256"]) == 64  # evidência hasheada, como a de execução
        assert (rig.ws.root / anexo["path"]).exists()
    # e nenhum deles virou sinal: anexo não é número
    declarados = [s for s in run["signals"] if s.get("source") != "derivado"]
    assert [s["name"] for s in declarados] == ["falhas"]
    # a análise que o pipeline já escreveu vira o corpo do documento
    assert corpo.strip() in (rig.ws.root / "ci/2026/github-101.md").read_text(
        encoding="utf-8")


def test_sem_manifesto_cai_na_convencao_e_diz_que_caiu(rig):
    """Convenção por nome de arquivo acerta hoje e quebra calada no dia em
    que alguém renomeia. Por isso ela avisa."""
    rig.fake.adicionar(101, artifact=_zip({
        "analysis.md": b"# relatorio\n",
        "erro.log": b"stacktrace\n",
    }))
    rig.post("/api/v1/ci/ingest")

    run = rig.get("/api/v1/ci/runs").json()["runs"][0]
    assert run["ingest_warning"]
    assert MANIFESTO in run["ingest_warning"]
    assert {a["kind"] for a in run["attachments"]} == {"analysis", "log"}
    # Nenhum sinal DECLARADO: número sem nome e sem unidade não é sinal, e
    # sem manifesto não há o que declarar. Os derivados são outra coisa — o
    # Arbites calcula sobre o que ele mesmo apurou (ADR 0019).
    assert [s for s in run["signals"] if s.get("source") != "derivado"] == []


def test_manifesto_de_versao_futura_recusa_aquele_run_e_segue(rig):
    rig.fake.adicionar(101, artifact=_zip({
        MANIFESTO: json.dumps({"version": 99, "signals": []}).encode("utf-8"),
    }))
    rig.fake.adicionar(102, artifact=_zip({MANIFESTO: manifesto([])}))

    resultado = rig.post("/api/v1/ci/ingest").json()
    assert resultado["ingested"] == ["github-102"]
    assert any(e["code"] == "manifest_version" for e in resultado["errors"])


def test_reindex_reconstroi_a_serie_a_partir_do_disco(rig):
    """O índice é descartável (ADR 0001): apagá-lo não pode apagar meses de
    série temporal. É por isso que o run é arquivo, não linha."""
    rig.fake.adicionar(101, artifact=_zip({
        MANIFESTO: manifesto([{"kind": "perf", "name": "lcp_ms", "value": 2400}]),
    }))
    rig.post("/api/v1/ci/ingest")

    from arbites.indexer import reindex_full
    conn = rig.app.state.conn
    conn.execute("DELETE FROM ci_runs")
    conn.execute("DELETE FROM ci_signals")
    conn.commit()
    reindex_full(rig.ws, conn)

    assert rig.get("/api/v1/ci/signals/lcp_ms").json()["count"] == 1
