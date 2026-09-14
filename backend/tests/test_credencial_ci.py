"""Credencial que expira ou é revogada vira problema VISÍVEL (change 0157).

A credencial vai falhar um dia, por desenho: o fine-grained expira em no
máximo 366 dias e o dono da organização pode revogar quando quiser. O defeito
que estes testes cercam não é a falha — é ela acontecer em SILÊNCIO, com
alguém descobrindo semanas depois que a observabilidade congelou.
"""

from datetime import date, timedelta

import pytest
import yaml
from conftest import login_admin
from fastapi.testclient import TestClient
from test_ci_ingest import FakeGitHub, FakeTokenStore, _zip, manifesto

from arbites.api import create_app
from arbites.ci import CIError, _e_rate_limit, _motivo
from arbites.ci_credential import CredentialState
from arbites.ci_ingest import MANIFESTO


class RespostaFalsa:
    def __init__(self, status, corpo="", headers=None):
        self.status_code = status
        self.text = corpo
        self.headers = headers or {}


def _monta(ws):
    config = ws.config()
    config["observability"] = {
        "sources": [{"provider": "github", "repo": "org/app"}],
    }
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


@pytest.fixture()
def rig(ws):
    client = _monta(ws)
    yield client
    client.__exit__(None, None, None)


def _daqui(dias: int) -> str:
    return (date.today() + timedelta(days=dias)).isoformat()


# -- 403 é ambíguo: rate limit ou permissão ---------------------------------


def test_403_com_cota_zerada_e_rate_limit_403_sem_cota_e_credencial():
    """Tratar todo 403 como rate limit faria a ferramenta tentar de novo para
    sempre contra um token revogado — em silêncio, que é o defeito."""
    assert _e_rate_limit(RespostaFalsa(403, "", {"x-ratelimit-remaining": "0"}))
    assert _e_rate_limit(RespostaFalsa(403, '{"message": "API rate limit exceeded"}'))
    assert _e_rate_limit(RespostaFalsa(403, "", {"retry-after": "60"}))
    assert not _e_rate_limit(RespostaFalsa(
        403, '{"message": "Resource not accessible by personal access token"}',
        {"x-ratelimit-remaining": "4980"}))


def test_motivo_repassa_a_frase_do_provedor():
    """'Bad credentials' e 'Resource not accessible' pedem ações diferentes
    de quem lê; inventar um motivo nosso apagaria a diferença."""
    assert _motivo('{"message": "Bad credentials"}') == "Bad credentials"
    assert _motivo("nao e json") == "nao e json"
    assert _motivo("") == "sem detalhe"


# -- o aviso chega ANTES de expirar -----------------------------------------


def test_credencial_perto_de_expirar_aparece_em_problemas_antes(rig):
    rig.put("/api/v1/settings/github/token",
            json={"token": "ghp_x", "expires_at": _daqui(5)})

    problemas = rig.get("/api/v1/warnings").json()
    aviso = next(p for p in problemas if p["code"] == "ci_credential_expiring")
    assert "expira em 5 dias" in aviso["message"]
    # e vem PRIMEIRO: bloqueia a ingestão inteira, não um arquivo só
    assert problemas[0]["code"] == "ci_credential_expiring"


def test_credencial_com_folga_nao_polui_a_tela(rig):
    rig.put("/api/v1/settings/github/token",
            json={"token": "ghp_x", "expires_at": _daqui(200)})
    codigos = {p["code"] for p in rig.get("/api/v1/warnings").json()}
    assert "ci_credential_expiring" not in codigos


def test_credencial_ja_expirada_diz_ha_quantos_dias(rig):
    rig.put("/api/v1/settings/github/token",
            json={"token": "ghp_x", "expires_at": _daqui(-3)})
    aviso = next(p for p in rig.get("/api/v1/warnings").json()
                 if p["code"] == "ci_credential_expiring")
    assert "expirou há 3 dias" in aviso["message"]


def test_token_sem_validade_informada_nao_inventa_uma(rig):
    """Quem usa um classic sem expiração não é avisado de nada — inventar uma
    data seria pior que não ter."""
    rig.put("/api/v1/settings/github/token", json={"token": "ghp_x"})
    estado = rig.get("/api/v1/settings/github/token").json()
    assert estado["expires_at"] is None
    assert estado["days_until_expiry"] is None
    assert estado["healthy"] is True


# -- recusa vira problema, não linha de log ---------------------------------


def test_recusa_do_provedor_vira_problema_com_o_motivo(ws):
    credencial = CredentialState(ws)
    credencial.registrar_recusa(401, "Bad credentials")

    problema = credencial.problemas(True)[0]
    assert problema["code"] == "ci_credential_refused"
    assert "Bad credentials" in problema["message"]
    # e diz que a ingestão PAROU por isso — o ponto inteiro da change
    assert "PARADA" in problema["message"]
    assert "não é ausência de execução nova" in problema["message"]


def test_parada_por_credencial_nao_se_confunde_com_sem_run_novo(rig):
    """Os dois estados parecem iguais na tela — nenhum dado novo — e pedem
    ações opostas: um exige repor o token, o outro exige não fazer nada."""
    rig.fake.adicionar(101, artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.falhar_em = {101}
    rig.fake.erro = CIError("bad_credential", "o GitHub recusou a credencial", 409)

    parada = rig.post("/api/v1/ci/ingest").json()
    assert parada["stopped"] == "bad_credential"

    # sem run novo: nenhuma parada anunciada
    rig.fake.falhar_em = set()
    rig.post("/api/v1/ci/ingest")
    silencio = rig.post("/api/v1/ci/ingest").json()
    assert silencio["ingested"] == []
    assert "stopped" not in silencio


def test_sucesso_apaga_a_recusa_anterior(ws):
    """Um 403 antigo não pode virar problema eterno na tela."""
    credencial = CredentialState(ws)
    credencial.registrar_recusa(403, "revogado")
    assert credencial.problemas(True)

    credencial.registrar_sucesso()
    assert [p for p in credencial.problemas(True)
            if p["code"] == "ci_credential_refused"] == []


def test_repor_a_credencial_retoma_do_ponto_em_que_parou(rig):
    """A marca d'água é o disco: repor o token traz o intervalo inteiro, não
    só o run mais recente."""
    for run_id in (101, 102, 103):
        rig.fake.adicionar(run_id, artifact=_zip({MANIFESTO: manifesto([])}))
    rig.fake.falhar_em = {101, 102, 103}
    rig.fake.erro = CIError("bad_credential", "recusado", 409)
    assert rig.post("/api/v1/ci/ingest").json()["stopped"] == "bad_credential"

    rig.fake.falhar_em = set()
    rig.put("/api/v1/settings/github/token",
            json={"token": "ghp_novo", "expires_at": _daqui(300)})

    retomada = rig.post("/api/v1/ci/ingest").json()
    assert sorted(retomada["ingested"]) == [
        "github-101", "github-102", "github-103"]
    # e o problema saiu da tela junto com a troca do token
    assert [p for p in rig.get("/api/v1/warnings").json()
            if p["code"].startswith("ci_credential")] == []


def test_estado_corrompido_nao_derruba_a_instancia(ws):
    credencial = CredentialState(ws)
    credencial.caminho.parent.mkdir(parents=True, exist_ok=True)
    credencial.caminho.write_text("{isto não é json", encoding="utf-8")
    assert credencial.status(True)["configured"] is True
    assert credencial.problemas(True) == []
