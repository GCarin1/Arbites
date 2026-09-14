"""Teste que VIROU instável (change 0159).

Era o vão registrado na change 0155: o manifesto declara medida AGREGADA, e
"2 cenários falharam" não responde *qual* virou instável. Instabilidade é por
cenário e não aparece em média nenhuma — um teste que passa, falha e passa de
novo some numa taxa de sucesso e continua corroendo a confiança na suíte.
"""

import json

import pytest
import yaml
from conftest import login_admin
from fastapi.testclient import TestClient
from test_ci_ingest import FakeGitHub, FakeTokenStore, _zip, manifesto

from arbites.api import create_app
from arbites.ci_ingest import MANIFESTO


def _cucumber(cenarios: list[tuple[str, str, str | None]]) -> bytes:
    """[(nome, status, ct)] → um Cucumber JSON de uma feature."""
    return json.dumps([{
        "name": "Checkout",
        "elements": [
            {"name": nome, "status": status,
             "tags": ([{"name": f"@{ct}"}] if ct else []),
             "steps": [{"result": {"status": status}}]}
            for nome, status, ct in cenarios
        ],
    }]).encode("utf-8")


def _artifact(cenarios, declarado=True) -> bytes:
    anexos = [{"kind": "cucumber", "path": "cucumber.json"}] if declarado else []
    return _zip({
        MANIFESTO: manifesto([], anexos),
        "cucumber.json": _cucumber(cenarios),
    })


@pytest.fixture()
def rig(ws):
    config = ws.config()
    config["observability"] = {"sources": [{"provider": "github", "repo": "org/app"}]}
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    fake = FakeGitHub()
    app = create_app(ws.root, watch=False,
                     github_client=fake, token_store=FakeTokenStore())
    client = TestClient(app)
    client.__enter__()
    login_admin(client)
    client.fake = fake
    client.ws = ws
    yield client
    client.__exit__(None, None, None)


def _ha(dias: int) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(days=dias)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _painel(rig, dias=30):
    return rig.get(f"/api/v1/ci/observability?days={dias}").json()


# -- ingestão por cenário ----------------------------------------------------


def test_cucumber_do_artifact_vira_resultado_por_cenario(rig):
    rig.fake.adicionar(101, started=_ha(2), artifact=_artifact([
        ("pagamento aprovado", "passed", "CT-0001"),
        ("pagamento recusado", "failed", "CT-0002"),
    ]))
    rig.post("/api/v1/ci/ingest")

    linhas = rig.app.state.conn.execute(
        "SELECT scenario, testcase_id, status FROM ci_scenarios ORDER BY scenario"
    ).fetchall()
    assert [dict(x) for x in linhas] == [
        {"scenario": "pagamento aprovado", "testcase_id": "CT-0001",
         "status": "passed"},
        {"scenario": "pagamento recusado", "testcase_id": "CT-0002",
         "status": "failed"},
    ]


def test_cucumber_reconhecido_por_convencao_quando_nao_declarado(rig):
    """Sem `kind: cucumber` no manifesto, o nome do arquivo ainda resolve —
    o mesmo fallback que já vale para print e log."""
    rig.fake.adicionar(101, started=_ha(2),
                       artifact=_artifact([("x", "passed", None)], declarado=False))
    rig.post("/api/v1/ci/ingest")
    assert rig.app.state.conn.execute(
        "SELECT COUNT(*) c FROM ci_scenarios").fetchone()["c"] == 1


def test_artifact_sem_cucumber_nao_inventa_cenario(rig):
    rig.fake.adicionar(101, started=_ha(2), artifact=_zip({MANIFESTO: manifesto([])}))
    rig.post("/api/v1/ci/ingest")
    assert rig.app.state.conn.execute(
        "SELECT COUNT(*) c FROM ci_scenarios").fetchone()["c"] == 0


# -- instabilidade -----------------------------------------------------------


def test_cenario_que_passa_e_falha_no_periodo_e_instavel(rig):
    for i, status in enumerate(["passed", "failed", "passed"]):
        rig.fake.adicionar(100 + i, started=_ha(6 - i * 2),
                           artifact=_artifact([("flapando", status, "CT-0001")]))
    rig.post("/api/v1/ci/ingest")

    instaveis = _painel(rig)["flaky"]
    assert len(instaveis) == 1
    assert instaveis[0]["scenario"] == "flapando"
    assert instaveis[0]["failures"] == 1
    assert instaveis[0]["flips"] == 2  # passed→failed→passed


def test_cenario_sempre_verde_ou_sempre_vermelho_nao_e_instavel(rig):
    """Falhar sempre é um defeito, não instabilidade — e chamar de instável o
    que quebrou de vez faria alguém re-executar em vez de corrigir."""
    for i in range(3):
        rig.fake.adicionar(100 + i, started=_ha(6 - i * 2), artifact=_artifact([
            ("sempre verde", "passed", None),
            ("quebrado de vez", "failed", None),
        ]))
    rig.post("/api/v1/ci/ingest")
    assert _painel(rig)["flaky"] == []


def test_o_que_mudou_so_anuncia_quem_VIROU_instavel(rig):
    """"Está instável" não é notícia para quem já sabe. A notícia é que estava
    estável no período anterior e não está mais."""
    # período ANTERIOR (40 e 36 dias atrás): já balançava
    for i, status in enumerate(["passed", "failed"]):
        rig.fake.adicionar(200 + i, started=_ha(40 - i * 4),
                           artifact=_artifact([("velho conhecido", status, None)]))
    # período ATUAL: o velho conhecido continua balançando, e um novo começa
    for i, (velho, novo) in enumerate([("passed", "passed"), ("failed", "failed")]):
        rig.fake.adicionar(300 + i, started=_ha(6 - i * 2), artifact=_artifact([
            ("velho conhecido", velho, None),
            ("recem chegado", novo, None),
        ]))
    rig.post("/api/v1/ci/ingest?limit=100")

    painel = _painel(rig)
    balancando = {f["scenario"]: f for f in painel["flaky"]}
    assert set(balancando) == {"velho conhecido", "recem chegado"}
    assert balancando["velho conhecido"]["newly_flaky"] is False
    assert balancando["recem chegado"]["newly_flaky"] is True

    anunciados = [m for m in painel["changes"] if m["kind"] == "flaky"]
    assert len(anunciados) == 1
    assert "recem chegado" in anunciados[0]["text"]
    assert "virou instável" in anunciados[0]["text"]


def test_o_anuncio_usa_o_caso_de_teste_quando_a_tag_existe(rig):
    """A tag @CT-XXXX é o que liga cenário a caso (ADR 0003) — quando ela
    existe, quem lê quer o CT, não o nome do cenário."""
    for i, status in enumerate(["passed", "failed"]):
        rig.fake.adicionar(100 + i, started=_ha(6 - i * 2),
                           artifact=_artifact([("qualquer nome", status, "CT-0042")]))
    rig.post("/api/v1/ci/ingest")

    anuncio = next(m for m in _painel(rig)["changes"] if m["kind"] == "flaky")
    assert anuncio["text"].startswith("CT-0042 virou instável")
    assert anuncio["testcase_id"] == "CT-0042"


def test_o_anuncio_aponta_a_execucao_para_a_descida_continuar(rig):
    for i, status in enumerate(["passed", "failed"]):
        rig.fake.adicionar(100 + i, started=_ha(6 - i * 2),
                           artifact=_artifact([("instavel", status, None)]))
    rig.post("/api/v1/ci/ingest")

    anuncio = next(m for m in _painel(rig)["changes"] if m["kind"] == "flaky")
    assert anuncio["run_id"] == "github-101"
    assert rig.get(f"/api/v1/ci/runs/{anuncio['run_id']}").status_code == 200


def test_reindex_reconstroi_os_cenarios_do_disco(rig):
    """Como todo o resto: o arquivo é a verdade, o índice é descartável."""
    for i, status in enumerate(["passed", "failed"]):
        rig.fake.adicionar(100 + i, started=_ha(6 - i * 2),
                           artifact=_artifact([("instavel", status, None)]))
    rig.post("/api/v1/ci/ingest")

    from arbites.indexer import reindex_full
    conn = rig.app.state.conn
    conn.execute("DELETE FROM ci_scenarios")
    conn.commit()
    reindex_full(rig.ws, conn)

    assert len(_painel(rig)["flaky"]) == 1
