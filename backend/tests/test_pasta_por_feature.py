"""CTs criados pela sincronização espelham a árvore dos `.feature` (0171).

Antes todos os CTs de todos os `.feature` caíam num diretório só
(`automacao/<alvo>/`): um repositório com dezenas de features virava uma
lista chapada de centenas de arquivos, sem nenhuma pista de onde cada caso
mora no projeto automatizado.
"""

import pytest
from conftest import logged_in_client

from arbites.feature_sync import pasta_do_cenario, prefixo_estatico

GLOB = "features/**/*.feature"

FEATURE = """Feature: Login
  Scenario: entra com credencial valida
    Given a tela de login
    When informo a credencial
    Then entro no sistema
"""


def test_o_prefixo_estatico_do_glob_sai_do_caminho():
    assert prefixo_estatico(GLOB) == "features"
    assert prefixo_estatico("*.feature") == ""
    assert prefixo_estatico("tests/e2e/**/*.feature") == "tests/e2e"


@pytest.mark.parametrize("caminho,esperado", [
    ("features/login/login.feature", "login/login"),
    ("features/checkout.feature", "checkout"),
    ("features/web/b2b/pedido.feature", "web/b2b/pedido"),
    ("login.feature", "login"),
])
def test_uma_pasta_por_arquivo_feature(caminho, esperado):
    assert pasta_do_cenario(caminho, GLOB) == esperado


def test_caminho_para_fora_nao_escapa_da_area():
    """Path traversal morre aqui antes de chegar ao `_safe_area_dir`."""
    assert pasta_do_cenario("../../etc/passwd.feature", GLOB) == "etc/passwd"


def _alvo(tmp_path, nome="Teste"):
    raiz = tmp_path / "projeto"
    for rel in ("features/login/login.feature", "features/web/b2b/pedido.feature"):
        caminho = raiz / rel
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(FEATURE, encoding="utf-8")
    return {"name": nome, "kind": "behave", "local_path": str(raiz),
            "features_glob": GLOB}


def test_sincronizar_cria_o_CT_dentro_da_pasta_da_feature(ws, tmp_path):
    with logged_in_client(ws) as client:
        assert client.put(
            "/api/v1/targets", json={"targets": [_alvo(tmp_path)]}
        ).status_code == 200
        r = client.post("/api/v1/automation/features-sync/apply", json={
            "target": "Teste",
            "create": [
                {"feature_path": "features/login/login.feature",
                 "scenario_name": "entra com credencial valida"},
                {"feature_path": "features/web/b2b/pedido.feature",
                 "scenario_name": "entra com credencial valida"},
            ],
        })
        assert r.status_code == 200, r.text
        criados = r.json()["created"]
        assert len(criados) == 2
        caminhos = sorted(
            client.get(f"/api/v1/testcases/{ct}").json()["path"] for ct in criados
        )
        assert caminhos[0].startswith("testcases/automacao/teste/login/login/")
        assert caminhos[1].startswith("testcases/automacao/teste/web/b2b/pedido/")


def test_a_pasta_informada_continua_valendo_como_raiz(ws, tmp_path):
    """Escolher a pasta no modal não desliga o espelhamento: ela vira a raiz."""
    with logged_in_client(ws) as client:
        assert client.put(
            "/api/v1/targets", json={"targets": [_alvo(tmp_path)]}
        ).status_code == 200
        r = client.post("/api/v1/automation/features-sync/apply", json={
            "target": "Teste", "folder": "regressao",
            "create": [{"feature_path": "features/login/login.feature",
                        "scenario_name": "entra com credencial valida"}],
        })
        assert r.status_code == 200, r.text
        ct = r.json()["created"][0]
        caminho = client.get(f"/api/v1/testcases/{ct}").json()["path"]
        assert caminho.startswith("testcases/regressao/login/login/")
