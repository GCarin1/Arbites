"""Exceção desconhecida não vira traceback na resposta (change 0185).

Quem clicou em "Buscar execuções" e caiu num erro de TLS recebeu 500 com uma
parede de stack trace: o motivo real (o certificado) estava enterrado no meio
de sessenta linhas de caminho de biblioteca, e nada dizia o que fazer. O
traceback é para quem corrige, e o lugar dele é o log.
"""

import pytest
from conftest import login_admin
from fastapi.testclient import TestClient

from arbites.api import create_app


ROTA = "/api/v1/ci/observability?days=30"


@pytest.fixture()
def cliente_que_explode(ws, monkeypatch):
    """Uma rota REAL levantando exceção não prevista, como faria um defeito
    novo. Rota de verdade e não inventada: uma registrada depois do mount da
    SPA cairia no estático e responderia 404, provando nada."""
    from arbites import ci_ingest

    def explode(*a, **k):
        raise RuntimeError("segredo: senha=hunter2 em /caminho/interno.db")

    monkeypatch.setattr(ci_ingest, "painel", explode)
    app = create_app(ws.root, watch=False)
    with TestClient(app, raise_server_exceptions=False) as client:
        client.ws = ws
        login_admin(client)
        yield client


def test_a_resposta_e_json_limpo_e_nao_traceback(cliente_que_explode):
    r = cliente_que_explode.get(ROTA)
    assert r.status_code == 500
    corpo = r.json()
    assert corpo["error"]["code"] == "internal_error"
    assert "Traceback" not in r.text


def test_a_resposta_nao_repassa_a_mensagem_da_excecao(cliente_que_explode):
    """Uma exceção qualquer pode carregar caminho, SQL ou credencial — e esta
    resposta sai para o navegador."""
    texto = cliente_que_explode.get(ROTA).text
    assert "hunter2" not in texto
    assert "/caminho/interno.db" not in texto


def test_o_traceback_vai_para_o_log_com_a_mesma_marca(cliente_que_explode, capsys):
    """A marca amarra a resposta à linha do log: sem ela, "está no log" manda
    procurar agulha no palheiro."""
    capsys.readouterr()
    marca = cliente_que_explode.get(ROTA).json()["error"]["trace_id"]
    saida = capsys.readouterr()
    registro = saida.out + saida.err
    assert f"[arbites:{marca}]" in registro
    assert "RuntimeError" in registro
    assert "hunter2" in registro  # o detalhe existe — só não na resposta


def test_cada_falha_tem_marca_propria(cliente_que_explode):
    a = cliente_que_explode.get(ROTA).json()["error"]["trace_id"]
    b = cliente_que_explode.get(ROTA).json()["error"]["trace_id"]
    assert a != b


def test_erros_previstos_continuam_com_a_mensagem_deles(ws):
    """A rede de segurança não pode engolir o que já era explicado: um erro
    de domínio continua dizendo o que dizia."""
    with TestClient(create_app(ws.root, watch=False)) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        r = client.post("/api/v1/auth/login",
                        json={"email": "nao@existe.test", "password": "x" * 12})
        assert r.status_code == 401
        assert r.json()["error"]["code"] != "internal_error"
