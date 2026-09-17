"""A busca varre só a LACUNA da janela pedida (change 0190).

O medo era justo: "se eu já busquei 30 dias e depois peço 90, ele vai buscar
os 90 de novo?". Buscar de novo não duplicava — a chave do run é o nome do
arquivo, e ingerir duas vezes reescreve o mesmo documento — mas custava, e
custava toda vez.

E havia algo pior escondido: a busca parava na primeira página inteiramente
conhecida, com o comentário "o passado está coberto". Não estava. Para quem
tinha 30 dias no disco e pedia 90, a primeira página era toda conhecida, a
busca parava ali, e os 60 dias mais antigos NUNCA chegavam.
"""

from __future__ import annotations

from arbites import ci_cobertura


# --- a conta das lacunas ----------------------------------------------------


def test_sem_nada_coberto_a_lacuna_e_a_janela_inteira():
    assert ci_cobertura.lacunas([], "2026-01-01", "2026-02-01") == [
        ("2026-01-01", "2026-02-01")]


def test_janela_ja_coberta_nao_tem_lacuna():
    """O caso de clicar "Buscar" duas vezes seguidas: zero listagem."""
    coberto = [["2026-01-01", "2026-03-01"]]

    assert ci_cobertura.lacunas(coberto, "2026-01-15", "2026-02-01") == []


def test_pedir_90_tendo_30_busca_so_os_60_que_faltam():
    """O pedido, na letra: não deve chamar os 90, deve chamar os outros 60."""
    coberto = [["2026-02-01", "2026-03-01"]]  # os 30 recentes

    faltando = ci_cobertura.lacunas(coberto, "2026-01-01", "2026-03-01")

    assert faltando == [("2026-01-01", "2026-02-01")]


def test_buraco_no_meio_vira_uma_lacuna_propria():
    coberto = [["2026-01-01", "2026-01-10"], ["2026-01-20", "2026-02-01"]]

    assert ci_cobertura.lacunas(coberto, "2026-01-01", "2026-02-01") == [
        ("2026-01-10", "2026-01-20")]


def test_intervalos_que_se_tocam_viram_um_so():
    fundido = ci_cobertura.fundir(
        [["2026-01-10", "2026-01-20"], ["2026-01-01", "2026-01-12"]])

    assert fundido == [["2026-01-01", "2026-01-20"]]


def test_intervalos_separados_continuam_separados():
    """Fundir dois intervalos com buraco entre eles afirmaria ter olhado um
    pedaço que ninguém olhou — e ele nunca mais seria varrido."""
    fundido = ci_cobertura.fundir(
        [["2026-01-01", "2026-01-05"], ["2026-01-20", "2026-01-25"]])

    assert len(fundido) == 2


# --- o registro no disco ----------------------------------------------------


def test_a_cobertura_e_por_fonte(ws):
    a = {"provider": "github", "repo": "org/front", "workflow": None}
    b = {"provider": "github", "repo": "org/back", "workflow": None}
    ci_cobertura.registrar(ws, a, "2026-01-01", "2026-02-01")

    assert ci_cobertura.cobertura_da_fonte(ws, a)
    assert ci_cobertura.cobertura_da_fonte(ws, b) == []


def test_o_workflow_faz_parte_da_identidade_da_fonte(ws):
    """Varrer filtrando por um workflow não diz nada sobre os outros."""
    um = {"provider": "github", "repo": "org/t", "workflow": "smoke.yml"}
    todos = {"provider": "github", "repo": "org/t", "workflow": None}
    ci_cobertura.registrar(ws, um, "2026-01-01", "2026-02-01")

    assert ci_cobertura.cobertura_da_fonte(ws, todos) == []


def test_arquivo_de_cobertura_corrompido_responde_nada_coberto(ws):
    """Degradar para trabalho a mais é sempre melhor que para trabalho a
    menos: perder a cobertura custa tempo, nunca dado."""
    fonte = {"provider": "github", "repo": "org/t", "workflow": None}
    ci_cobertura.registrar(ws, fonte, "2026-01-01", "2026-02-01")
    ci_cobertura.caminho(ws).write_text("{ isto não é json", encoding="utf-8")

    assert ci_cobertura.cobertura_da_fonte(ws, fonte) == []


def test_esquecer_apaga_so_a_fonte_pedida(ws):
    a = {"provider": "github", "repo": "org/a", "workflow": None}
    b = {"provider": "github", "repo": "org/b", "workflow": None}
    ci_cobertura.registrar(ws, a, "2026-01-01", "2026-02-01")
    ci_cobertura.registrar(ws, b, "2026-01-01", "2026-02-01")

    ci_cobertura.esquecer(ws, a)

    assert ci_cobertura.cobertura_da_fonte(ws, a) == []
    assert ci_cobertura.cobertura_da_fonte(ws, b)


# --- de ponta a ponta -------------------------------------------------------

import pytest  # noqa: E402
import yaml  # noqa: E402

from arbites.api import create_app  # noqa: E402
from conftest import login_admin  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from test_ci_ingest import (  # noqa: E402
    MANIFESTO, FakeGitHub, FakeTokenStore, _ha_dias, _zip, manifesto,
)


@pytest.fixture()
def rig(ws):
    fake = FakeGitHub()
    config = ws.config()
    config["observability"] = {
        "sources": [{"provider": "github", "repo": "org/app"}],
        "max_runs_per_poll": 50,
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8")
    app = create_app(ws.root, watch=False,
                     github_client=fake, token_store=FakeTokenStore())
    with TestClient(app) as client:
        login_admin(client)
        client.fake = fake
        client.ws = ws
        yield client


def _artefato():
    return _zip({MANIFESTO: manifesto([])})


def _dias_da_janela(janela: str) -> int:
    from datetime import date

    ini, fim = janela.split("..")
    return (date.fromisoformat(fim) - date.fromisoformat(ini)).days


def test_segunda_busca_do_mesmo_periodo_so_reconfere_a_borda(rig):
    """O medo do relatório, respondido: buscar de novo não refaz o trabalho.

    Não é ZERO listagem — a borda recente é reconferida de propósito (ver
    MARGEM_HORAS) —, mas é uma janela de dois dias no lugar de trinta.
    """
    rig.fake.adicionar(101, artifact=_artefato(), started=_ha_dias(10))
    rig.post("/api/v1/ci/ingest?days=30")
    primeira = rig.fake.listagens[-1]
    assert _dias_da_janela(primeira) == 30

    segunda_resposta = rig.post("/api/v1/ci/ingest?days=30").json()

    assert segunda_resposta["ingested"] == []
    assert _dias_da_janela(rig.fake.listagens[-1]) <= 3
    assert rig.fake.chamadas_de_download == 1  # o artifact não volta a descer


def test_a_borda_recente_e_sempre_reconferida(rig):
    """Um run começado às 23h e concluído às 01h não aparece na varredura da
    véspera — a listagem pede `status=completed` e o filtro do provedor é
    pela data de CRIAÇÃO. Se a véspera já constasse coberta, esse run não
    apareceria mais nunca."""
    rig.fake.adicionar(101, artifact=_artefato(), started=_ha_dias(10))
    rig.post("/api/v1/ci/ingest?days=30")

    rig.fake.adicionar(102, artifact=_artefato(), started=_ha_dias(0.2))
    segunda = rig.post("/api/v1/ci/ingest?days=30").json()

    assert segunda["ingested"] == ["github-102"]


def test_ampliar_o_periodo_busca_so_o_que_faltava(rig):
    """30 depois 90: os 60 do meio entram, e a janela recente não é
    re-listada."""
    rig.fake.adicionar(101, artifact=_artefato(), started=_ha_dias(10))
    rig.fake.adicionar(202, artifact=_artefato(), started=_ha_dias(60))
    rig.post("/api/v1/ci/ingest?days=30")

    ampliado = rig.post("/api/v1/ci/ingest?days=90").json()

    assert ampliado["ingested"] == ["github-202"]
    # Nenhuma varredura cobre os 90 dias: o pedaço já coberto fica de fora.
    assert all(_dias_da_janela(j) < 90 for j in rig.fake.listagens[-2:])
    assert rig.fake.chamadas_de_download == 2  # só o run novo desceu


def test_o_passado_antigo_deixa_de_ser_inalcancavel(rig):
    """O defeito escondido: a busca parava na primeira página inteiramente
    conhecida, dizendo "o passado está coberto". Para quem tinha 30 dias no
    disco e pedia 90, ela parava na página 1 e os 60 mais antigos nunca
    chegavam."""
    for i in range(1, 61):
        rig.fake.adicionar(i, artifact=_artefato(), started=_ha_dias(5))
    rig.post("/api/v1/ci/ingest?days=30&limit=200")

    antigo = 900
    rig.fake.adicionar(antigo, artifact=_artefato(), started=_ha_dias(70))
    resultado = rig.post("/api/v1/ci/ingest?days=90&limit=200").json()

    assert f"github-{antigo}" in resultado["ingested"]


def test_reconferir_ignora_a_cobertura_sem_apagar_nada(rig):
    """Quem desconfia do que está na tela tem de poder mandar reconferir —
    e reconferir não pode custar o histórico."""
    rig.fake.adicionar(101, artifact=_artefato(), started=_ha_dias(10))
    rig.post("/api/v1/ci/ingest?days=30")
    downloads = rig.fake.chamadas_de_download

    refeito = rig.post("/api/v1/ci/ingest?days=30&refresh=true").json()

    assert refeito["scanned"], "reconferir tem de varrer de verdade"
    assert refeito["ingested"] == []  # já está no disco: nada é rebaixado
    assert rig.fake.chamadas_de_download == downloads
    assert len(rig.get("/api/v1/ci/runs").json()["runs"]) == 1


def test_parada_no_meio_nao_registra_cobertura(rig):
    """Parar por limite de taxa e marcar o período como varrido deixaria
    para trás exatamente os runs que não chegaram."""
    from arbites import ci_cobertura

    rig.fake.adicionar(101, artifact=_artefato(), started=_ha_dias(10))
    rig.fake.adicionar(102, artifact=_artefato(), started=_ha_dias(11))
    rig.fake.falhar_em = {101, 102}

    rig.post("/api/v1/ci/ingest?days=30")

    fonte = {"provider": "github", "repo": "org/app", "workflow": None}
    assert ci_cobertura.cobertura_da_fonte(rig.ws, fonte) == []
