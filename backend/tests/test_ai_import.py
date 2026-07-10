"""Importação inteligente via IA (doc §1.1) — txt/md/xml livre → BDD preview."""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore
from arbites.api import create_app
from arbites.workspace import DEFAULT_CONFIG, Workspace

CONVERSION = {
    "folder": "login",
    "testcases": [
        {
            "title": "Login com credenciais válidas",
            "pre_condicoes": ["usuário cadastrado"],
            "passos": ["abrir a tela de login", "informar credenciais"],
            "resultado_esperado": "dashboard exibido",
        }
    ],
}


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


@pytest.fixture()
def client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "lmstudio", "model": "gemma-2-9b"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(CONVERSION, ensure_ascii=False)}}]},
        )
    )
    app = create_app(ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
                     ai_transport=transport, github_client=object())
    with TestClient(app) as c:
        c.ws = ws
        yield c


def test_import_ai_converts_free_text_to_bdd_preview(client):
    resp = client.post(
        "/api/v1/import/ai",
        files={"file": ("casos_login.txt", "1) login ok: abrir tela...", "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["preview"] is True and data["folder"] == "login"
    body = data["testcases"][0]["body"]
    assert "Scenario: Login com credenciais válidas" in body
    assert "Given usuário cadastrado" in body
    assert "When abrir a tela de login" in body
    assert "Then dashboard exibido" in body
    # nada gravado sem aceite
    assert client.get("/api/v1/testcases").json() == []

    # aceite = POST /testcases normal, na pasta sugerida
    ct = client.post(
        "/api/v1/testcases",
        json={"title": data["testcases"][0]["title"], "folder": data["folder"],
              "body": body},
    ).json()
    assert ct["path"].startswith("testcases/login/")


GHERKIN = """Feature: Pesquisa simples

Scenario: Realizar pesquisa com um termo válido
  Given que o usuário acessa a página inicial do Google
  When o usuário informa "OpenAI" no campo de pesquisa
  And clica no botão de pesquisa
  Then a página de resultados deve ser exibida
  And os resultados devem conter referências ao termo pesquisado"""


def test_import_gherkin_is_preserved_verbatim_without_ai(client):
    # arquivo já em BDD: NÃO deve passar pela IA (mock devolveria folder "login")
    # nem parafrasear — corpo idêntico ao enviado, só normalizando indentação.
    resp = client.post(
        "/api/v1/import/ai",
        files={"file": ("modelagem.txt", GHERKIN, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["folder"] == "pesquisa-simples"  # slug da Feature, não "login" da IA
    assert len(data["testcases"]) == 1
    body = data["testcases"][0]["body"]
    # Feature preservada (a IA trocava pelo título do cenário)
    assert "Feature: Pesquisa simples" in body
    # 'que' preservado, sem ponto final, sem capitalização forçada
    assert "Given que o usuário acessa a página inicial do Google" in body
    # os DOIS And preservados (a IA fundia o segundo Then/And num só)
    assert "And clica no botão de pesquisa" in body
    assert "Then a página de resultados deve ser exibida" in body
    assert "And os resultados devem conter referências ao termo pesquisado" in body
    # aceite grava o corpo verbatim
    ct = client.post(
        "/api/v1/testcases",
        json={"title": data["testcases"][0]["title"], "folder": data["folder"],
              "body": body},
    ).json()
    assert ct["path"].startswith("testcases/pesquisa-simples/")


GHERKIN_WITH_MD_HEADER_BETWEEN_SCENARIOS = """Feature: Pesquisa composta

Scenario: Pesquisar utilizando múltiplas palavras

Given que o usuário acessa a página inicial do Google

When o usuário pesquisa por "automação de testes selenium"

Then a página de resultados deve ser exibida

And devem existir resultados relacionados aos termos pesquisados

### CT04 - Pesquisa utilizando caracteres especiais

Feature: Pesquisa com caracteres especiais

Scenario: Pesquisar usando caracteres especiais

Given que o usuário acessa a página inicial do Google

When o usuário pesquisa por "@OpenAI"

Then a página de resultados deve ser exibida sem erros
"""


def test_import_gherkin_ignores_markdown_headers_between_scenarios(client):
    # regressão: "### CTxx - ..." usado como separador entre casos não pode
    # virar um passo colado no cenário anterior.
    resp = client.post(
        "/api/v1/import/ai",
        files={"file": ("casos.txt", GHERKIN_WITH_MD_HEADER_BETWEEN_SCENARIOS, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["testcases"]) == 2
    first_body = data["testcases"][0]["body"]
    assert "### CT04" not in first_body
    assert first_body.strip().endswith(
        "And devem existir resultados relacionados aos termos pesquisados"
    )
    second_body = data["testcases"][1]["body"]
    assert "Feature: Pesquisa com caracteres especiais" in second_body
    assert 'When o usuário pesquisa por "@OpenAI"' in second_body


def test_import_ai_rejects_unsupported_extension_and_empty(client):
    resp = client.post(
        "/api/v1/import/ai", files={"file": ("casos.pdf", b"%PDF", "application/pdf")}
    )
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "invalid_file"
    resp2 = client.post(
        "/api/v1/import/ai", files={"file": ("vazio.txt", "", "text/plain")}
    )
    assert resp2.status_code == 422 and resp2.json()["error"]["code"] == "empty_file"
