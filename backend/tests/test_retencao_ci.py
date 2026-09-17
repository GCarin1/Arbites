"""Retenção de artefato e sinal de CI (change 0156).

A aposta central: **sinal e anexo têm valores de vida diferentes.** O sinal é
barato e é o que faz a série; o anexo é caro e só interessa perto do evento.
O teste que importa é o do trade-off — o print de agosto vai embora e a
pergunta "a acessibilidade regrediu em agosto?" continua respondida.
"""

from datetime import datetime, timedelta, timezone

import pytest
import yaml
from conftest import login_admin
from fastapi.testclient import TestClient
from test_ci_ingest import FakeGitHub, FakeTokenStore, _zip, manifesto

from arbites.api import create_app
from arbites.ci_ingest import MANIFESTO
from arbites.ci_retencao import PADRAO_ANEXOS_DIAS, PADRAO_SINAIS_DIAS, janelas


def _monta(ws, retencao=None):
    config = ws.config()
    config["observability"] = {"sources": [{"provider": "github", "repo": "org/app"}]}
    if retencao:
        config["observability"]["retention"] = retencao
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
    return client


def _ha(dias: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


ARTIFACT = {
    MANIFESTO: manifesto(
        [{"kind": "a11y", "name": "violacoes_axe", "value": 7, "unit": "count"}],
        [{"kind": "screenshot", "path": "home.png"},
         {"kind": "log", "path": "run.log"}],
    ),
    "home.png": b"\x89PNG\r\n\x1a\n" + b"x" * 4000,
    "run.log": b"linha\n" * 500,
}


@pytest.fixture()
def rig(ws):
    client = _monta(ws, {"signals_days": 365, "attachments_days": 30})
    client.fake.adicionar(101, started=_ha(200), artifact=_zip(ARTIFACT))  # velho
    client.fake.adicionar(102, started=_ha(5), artifact=_zip(ARTIFACT))    # novo
    client.post("/api/v1/ci/ingest?days=3650")
    yield client
    client.__exit__(None, None, None)


def test_janelas_tem_padrao_explicito_e_sao_configuraveis(ws):
    assert janelas(ws) == {"signals_days": PADRAO_SINAIS_DIAS,
                           "attachments_days": PADRAO_ANEXOS_DIAS}
    assert PADRAO_SINAIS_DIAS > PADRAO_ANEXOS_DIAS  # o sinal vive mais. É a regra.

    cfg = ws.config()
    cfg["observability"] = {"retention": {"signals_days": 90, "attachments_days": 7}}
    ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    assert janelas(ws) == {"signals_days": 90, "attachments_days": 7}


def test_valor_invalido_cai_no_padrao_em_vez_de_apagar_tudo(ws):
    """Retenção zero ou negativa apagaria o histórico inteiro no primeiro
    clique — um erro de digitação no YAML não pode ter esse poder."""
    cfg = ws.config()
    cfg["observability"] = {"retention": {"signals_days": 0, "attachments_days": -5}}
    ws.config_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    assert janelas(ws) == {"signals_days": PADRAO_SINAIS_DIAS,
                           "attachments_days": PADRAO_ANEXOS_DIAS}


def test_previa_mostra_o_ocupado_e_o_que_seria_removido_antes_de_remover(rig):
    previa = rig.get("/api/v1/ci/retention").json()
    assert previa["usage"]["runs"] == 2
    assert previa["usage"]["attachments_bytes"] > previa["usage"]["documents_bytes"]

    alvos = [a["id"] for a in previa["would_remove"]["attachments"]]
    assert alvos == ["github-101"]           # só o velho
    assert previa["would_remove"]["runs"] == []  # 200 dias < janela de 365
    assert previa["would_remove"]["bytes"] > 0


def test_anexo_expira_e_a_serie_do_mesmo_periodo_continua_respondendo(rig):
    """O trade-off inteiro da change numa asserção: o print de 200 dias atrás
    vai embora e a pergunta sobre aquele período continua respondida."""
    antes = rig.get("/api/v1/ci/signals/violacoes_axe").json()
    assert antes["count"] == 2

    rig.post("/api/v1/ci/retention/apply")

    depois = rig.get("/api/v1/ci/signals/violacoes_axe").json()
    assert depois["count"] == 2          # a série sobreviveu inteira
    velho = rig.get("/api/v1/ci/runs/github-101").json()
    assert velho["attachments"] == []    # e o anexo se foi
    assert rig.get("/api/v1/ci/runs/github-102").json()["attachments"]


def test_previa_bate_com_o_que_e_executado(rig):
    previa = rig.get("/api/v1/ci/retention").json()["would_remove"]
    feito = rig.post("/api/v1/ci/retention/apply").json()["removed"]

    assert feito["attachments"] == [a["id"] for a in previa["attachments"]]
    assert feito["runs"] == [r["id"] for r in previa["runs"]]
    assert feito["bytes"] == previa["bytes"]


def test_limpeza_vai_para_a_lixeira_e_volta(rig):
    rig.post("/api/v1/ci/retention/apply")

    lixeira = rig.get("/api/v1/trash").json()
    nomes = [item["name"] for item in lixeira]
    assert "github-101" in nomes

    rig.post("/api/v1/trash/github-101/restore")
    assert (rig.ws.root / "ci" / _ha(200)[:4] / "github-101" / "home.png").exists()


def test_run_alem_da_janela_do_sinal_sai_inteiro(ws):
    cliente = _monta(ws, {"signals_days": 30, "attachments_days": 7})
    try:
        cliente.fake.adicionar(101, started=_ha(400), artifact=_zip(ARTIFACT))
        cliente.fake.adicionar(102, started=_ha(2), artifact=_zip(ARTIFACT))
        cliente.post("/api/v1/ci/ingest?days=3650")

        previa = cliente.get("/api/v1/ci/retention").json()["would_remove"]
        assert [r["id"] for r in previa["runs"]] == ["github-101"]

        cliente.post("/api/v1/ci/retention/apply")
        assert cliente.get("/api/v1/ci/runs/github-101").status_code == 404
        assert len(cliente.get("/api/v1/ci/runs").json()["runs"]) == 1
    finally:
        cliente.__exit__(None, None, None)


def test_nada_a_remover_nao_remove_nada(ws):
    cliente = _monta(ws, {"signals_days": 365, "attachments_days": 365})
    try:
        cliente.fake.adicionar(101, started=_ha(3), artifact=_zip(ARTIFACT))
        cliente.post("/api/v1/ci/ingest?days=3650")

        assert cliente.get("/api/v1/ci/retention").json()["would_remove"]["bytes"] == 0
        feito = cliente.post("/api/v1/ci/retention/apply").json()["removed"]
        assert feito["attachments"] == [] and feito["runs"] == []
        assert cliente.get("/api/v1/ci/runs/github-101").json()["attachments"]
    finally:
        cliente.__exit__(None, None, None)
