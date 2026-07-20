"""Banco de Lições Aprendidas — defeitos ganham causa/correção/prevenção,
filtráveis na UI e cruzados pela IA ao gerar CTs (não repetir o mesmo bug).
"""

import json

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from arbites.ai import AIKeyStore, find_relevant_lessons
from arbites.api import create_app
from arbites.indexer import connect
from arbites.workspace import DEFAULT_CONFIG, Workspace

GENERATED = {
    "testcases": [
        {
            "title": "Documento obrigatório vazio é rejeitado",
            "type": "manual",
            "priority": "high",
            "tags": [],
            "objetivo": "x",
            "pre_condicoes": [],
            "passos": ["Enviar cadastro sem o documento"],
            "resultado_esperado": "Erro de validação exibido",
        }
    ]
}


def test_defect_lesson_fields_persist_and_index(client):
    d = client.post(
        "/api/v1/defects",
        json={
            "title": "Bug #453",
            "severity": "high",
            "root_cause": "falta validação obrigatória de CPF",
            "fix": "campo obrigatório",
            "prevention": "sempre testar CPF vazio",
        },
    ).json()
    assert d["root_cause"] == "falta validação obrigatória de CPF"
    assert d["fix"] == "campo obrigatório"
    assert d["prevention"] == "sempre testar CPF vazio"

    fetched = client.get(f"/api/v1/defects/{d['id']}").json()
    assert fetched["prevention"] == "sempre testar CPF vazio"

    text = (client.ws.root / d["path"]).read_text(encoding="utf-8")
    assert "sempre testar CPF vazio" in text


def test_update_defect_can_add_lesson_later(client):
    d = client.post("/api/v1/defects", json={"title": "Sem lição ainda"}).json()
    assert d["root_cause"] is None
    updated = client.put(
        f"/api/v1/defects/{d['id']}",
        json={"root_cause": "causa X", "fix": "correção Y", "prevention": "prevenção Z"},
    ).json()
    assert updated["root_cause"] == "causa X"


def test_list_defects_has_lesson_filter(client):
    client.post(
        "/api/v1/defects",
        json={"title": "Com lição", "root_cause": "x", "prevention": "y"},
    )
    client.post("/api/v1/defects", json={"title": "Sem lição"})

    only_lessons = client.get("/api/v1/defects", params={"has_lesson": "true"}).json()
    assert [d["title"] for d in only_lessons] == ["Com lição"]

    all_defects = client.get("/api/v1/defects").json()
    assert len(all_defects) == 2


def test_find_relevant_lessons_matches_by_shared_keyword(client):
    client.post(
        "/api/v1/defects",
        json={
            "title": "Bug #453",
            "root_cause": "falta validação obrigatória de CPF",
            "prevention": "sempre testar CPF vazio",
        },
    )
    conn = connect(client.ws)
    lessons = find_relevant_lessons(
        conn, "Cadastro de cliente deve ter validação obrigatória dos documentos"
    )
    assert len(lessons) == 1
    assert lessons[0]["prevention"] == "sempre testar CPF vazio"

    # sem palavra-chave em comum (>=4 letras) -> nenhum resultado
    assert find_relevant_lessons(conn, "Tela de login com botão azul") == []

    # defeito SEM lição preenchida nunca aparece, mesmo com título batendo
    client.post("/api/v1/defects", json={"title": "Outro bug de validação obrigatória"})
    lessons2 = find_relevant_lessons(conn, "validação obrigatória")
    assert all(l["id"] != "" for l in lessons2)
    assert len(lessons2) == 1  # só o que tem root_cause/fix/prevention


class FakeAIKeyStore(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _recording_transport(content: str, sink: list):
    def handler(request: httpx.Request) -> httpx.Response:
        sink.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    return httpx.MockTransport(handler)


@pytest.fixture()
def lessons_client(tmp_path):
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [
            {"name": "local", "kind": "openai_compatible",
             "base_url": "http://localhost:1234/v1", "model": "qwen"},
        ],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    requests: list = []
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_recording_transport(json.dumps(GENERATED, ensure_ascii=False), requests),
        github_client=object(),
    )
    with TestClient(app) as c:
        c.ws = ws
        c.requests = requests
        yield c


def test_generate_testcases_injects_relevant_lessons_into_prompt(lessons_client):
    lessons_client.post(
        "/api/v1/defects",
        json={
            "title": "Bug #453",
            "severity": "high",
            "root_cause": "falta validação obrigatória de CPF",
            "fix": "campo obrigatório",
            "prevention": "sempre testar CPF vazio",
        },
    )
    story = lessons_client.post(
        "/api/v1/requirements",
        json={
            "kind": "story",
            "title": "Cadastro de cliente",
            "body": "Como usuário, quero que o cadastro exija validação"
                    " obrigatória dos documentos antes de salvar.",
        },
    ).json()

    resp = lessons_client.post(
        "/api/v1/ai/generate-testcases", json={"source": story["id"]}
    )
    assert resp.status_code == 200
    preview = resp.json()
    assert preview["lessons_used"] == [{"id": "DF-0001", "title": "Bug #453"}]

    # a lição foi de fato injetada no prompt enviado ao provider (não só
    # reportada na resposta — precisa comprovar que a IA recebeu o contexto)
    sent = lessons_client.requests[0]
    system_msg = next(m["content"] for m in sent["messages"] if m["role"] == "system")
    assert "falta validação obrigatória de CPF" in system_msg
    assert "sempre testar CPF vazio" in system_msg


def test_generate_testcases_no_lessons_used_when_no_match(lessons_client):
    lessons_client.post(
        "/api/v1/defects",
        json={
            "title": "Bug de outra área",
            "root_cause": "timeout no serviço de pagamento",
            "prevention": "mock do gateway em teste de carga",
        },
    )
    story = lessons_client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Tela de login", "body": "Autenticar com e-mail e senha."},
    ).json()

    resp = lessons_client.post(
        "/api/v1/ai/generate-testcases", json={"source": story["id"]}
    )
    assert resp.status_code == 200
    assert resp.json()["lessons_used"] == []
    sent = lessons_client.requests[0]
    system_msg = next(m["content"] for m in sent["messages"] if m["role"] == "system")
    assert "Lições aprendidas" not in system_msg


# ------------------------------------------------------- 0095 estruturadas

def test_structured_lesson_fields_persist_and_index(client):
    d = client.post(
        "/api/v1/defects",
        json={
            "title": "Token não expira",
            "root_cause": "comparação de data ingênua",
            "lesson_when": "ao comparar timestamps de expiração",
            "lesson_procedure": "usar datetime timezone-aware em UTC",
            "lesson_antipattern": "comparar datetime naive com aware",
        },
    ).json()
    assert d["lesson_when"] == "ao comparar timestamps de expiração"
    assert d["lesson_procedure"] == "usar datetime timezone-aware em UTC"
    assert d["lesson_antipattern"] == "comparar datetime naive com aware"

    fetched = client.get(f"/api/v1/defects/{d['id']}").json()
    assert fetched["lesson_antipattern"] == "comparar datetime naive com aware"
    text = (client.ws.root / d["path"]).read_text(encoding="utf-8")
    assert "timezone-aware" in text


def test_find_relevant_lessons_matches_structured_only(client):
    # defeito SEM root_cause, só com lição estruturada
    client.post(
        "/api/v1/defects",
        json={
            "title": "Bug de expiração",
            "lesson_when": "ao validar expiração de token de sessão",
            "lesson_antipattern": "comparar naive com aware",
        },
    )
    conn = connect(client.ws)
    lessons = find_relevant_lessons(conn, "Sessão deve validar expiração do token")
    assert len(lessons) == 1
    assert lessons[0]["lesson_when"] == "ao validar expiração de token de sessão"


def test_generate_prefers_structured_lesson_in_prompt(lessons_client):
    lessons_client.post(
        "/api/v1/defects",
        json={
            "title": "Bug #99",
            "root_cause": "causa antiga solta",
            "lesson_when": "ao validar documento obrigatório",
            "lesson_procedure": "exigir o campo antes de salvar",
            "lesson_antipattern": "salvar sem validar o documento",
        },
    )
    story = lessons_client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Cadastro",
              "body": "O cadastro deve exigir validação do documento obrigatório."},
    ).json()
    lessons_client.post("/api/v1/ai/generate-testcases", json={"source": story["id"]})
    sent = lessons_client.requests[0]
    system_msg = next(m["content"] for m in sent["messages"] if m["role"] == "system")
    # formato estruturado preferido (evite=/faça=), não o solto (causa=)
    assert "evite=salvar sem validar o documento" in system_msg
    assert "faça=exigir o campo antes de salvar" in system_msg
    assert "causa antiga solta" not in system_msg


def test_ai_structure_lesson_endpoint_is_preview(tmp_path):
    """POST /ai/structure-lesson devolve a lição estruturada em preview,
    sem gravar nada no defeito (o save fica a cargo do usuário)."""
    structured = {
        "lesson_when": "ao comparar datas de expiração",
        "lesson_procedure": "usar datetime timezone-aware em UTC",
        "lesson_antipattern": "comparar naive com aware",
    }
    ws = Workspace(tmp_path / "workspace")
    ws.ensure()
    config = dict(DEFAULT_CONFIG)
    config["ai"] = {
        "default_provider": "local",
        "providers": [{"name": "local", "kind": "openai_compatible",
                       "base_url": "http://localhost:1234/v1", "model": "qwen"}],
    }
    ws.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    app = create_app(
        ws.root, watch=False, ai_key_store=FakeAIKeyStore(),
        ai_transport=_recording_transport(json.dumps(structured, ensure_ascii=False), []),
        github_client=object(),
    )
    with TestClient(app) as c:
        d = c.post(
            "/api/v1/defects",
            json={"title": "Token não expira", "root_cause": "comparação ingênua"},
        ).json()
        resp = c.post(f"/api/v1/ai/structure-lesson/{d['id']}", json={})
        assert resp.status_code == 200, resp.text
        out = resp.json()
        assert out["preview"] is True
        assert out["lesson_procedure"] == "usar datetime timezone-aware em UTC"
        # preview não grava: o defeito segue sem os campos estruturados
        fetched = c.get(f"/api/v1/defects/{d['id']}").json()
        assert fetched["lesson_procedure"] is None
