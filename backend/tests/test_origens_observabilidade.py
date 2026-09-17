"""Declarar as origens da observabilidade pela tela (change 0173).

`observability.sources` só existia no `arbites.yaml`. Numa instalação nova a
aba respondia "nenhuma execução chegou ainda", o botão "Buscar execuções"
levantava `no_sources` — e não havia onde declarar uma origem sem abrir o
arquivo na mão.
"""

import pytest
from conftest import ADMIN_EMAIL, logged_in_client

from arbites import auth as auth_ops


def test_instalacao_nova_responde_lista_vazia(ws):
    with logged_in_client(ws) as client:
        r = client.get("/api/v1/ci/sources")
        assert r.status_code == 200
        assert r.json()["sources"] == []
        assert r.json()["max_runs_per_poll"] == 50


def test_declarar_uma_origem_grava_no_yaml(ws):
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/ci/sources", json={"sources": [
            {"repo": "org/repositorio", "workflow": "e2e.yml"}]})
        assert r.status_code == 200, r.text
        assert r.json()["sources"] == [
            {"provider": "github", "repo": "org/repositorio", "workflow": "e2e.yml"}]
        salvo = client.ws.config()["observability"]["sources"]
        assert salvo[0]["repo"] == "org/repositorio"


def test_workflow_e_artifact_vazios_nao_viram_chave(ws):
    """Vazio quer dizer "todos" — gravar "" faria a ingestão procurar um
    workflow de nome vazio e nunca achar nada."""
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/ci/sources", json={"sources": [
            {"repo": "org/repo", "workflow": "  ", "artifact": ""}]})
        assert r.status_code == 200, r.text
        fonte = r.json()["sources"][0]
        assert "workflow" not in fonte and "artifact" not in fonte


def test_origem_sem_repositorio_e_descartada(ws):
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/ci/sources", json={"sources": [
            {"repo": "   "}, {"repo": "org/valido"}]})
        assert [f["repo"] for f in r.json()["sources"]] == ["org/valido"]


def test_a_origem_declarada_e_a_que_a_ingestao_enxerga(ws):
    """Ida e volta real: o que a tela grava é o que o ingestor lê."""
    from arbites.ci_ingest import CIIngestor

    with logged_in_client(ws) as client:
        client.put("/api/v1/ci/sources", json={"sources": [
            {"repo": "org/repo", "workflow": "e2e.yml", "artifact": "cucumber"}]})
        ingestor = CIIngestor(client.ws, None, None)
        assert ingestor.fontes() == [{
            "provider": "github", "repo": "org/repo",
            "workflow": "e2e.yml", "artifact": "cucumber",
        }]


def test_escrever_exige_admin_e_ler_nao(ws):
    """A tela precisa dizer "nenhuma origem" a quem não pode declarar."""
    with logged_in_client(ws) as client:
        conn = client.app.state.auth
        auth_ops.create_user(conn, "leitor@arbites.test", "uma-senha-longa-1",
                             role="viewer", status="active")
    from fastapi.testclient import TestClient

    from arbites.api import create_app

    with TestClient(create_app(ws.root, watch=False)) as leitor:
        leitor.post("/api/v1/auth/login", json={
            "email": "leitor@arbites.test", "password": "uma-senha-longa-1"})
        assert leitor.get("/api/v1/ci/sources").status_code == 200
        r = leitor.put("/api/v1/ci/sources", json={"sources": [{"repo": "x/y"}]})
        assert r.status_code == 403
