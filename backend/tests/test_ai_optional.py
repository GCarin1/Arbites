"""Princípio 4 do intake: IA é opcional — plataforma 100% funcional sem
nenhum provider (spec ai-assist, critério 3)."""


def test_platform_fully_functional_with_no_providers(client):
    # client padrão: arbites.yaml default tem ai.default_provider: null
    providers = client.get("/api/v1/ai/providers").json()
    assert providers["default_provider"] is None
    assert providers["providers"] == []

    # funções de IA desabilitadas com erro claro…
    resp = client.post("/api/v1/ai/generate-testcases", json={"source": "texto"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ai_disabled"

    # …e TODO o resto opera normalmente
    epic = client.post(
        "/api/v1/requirements", json={"kind": "epic", "title": "Auth"}
    ).json()
    story = client.post(
        "/api/v1/requirements",
        json={"kind": "story", "title": "Login", "epic": epic["id"]},
    ).json()
    ct = client.post(
        "/api/v1/testcases",
        json={"title": "Login ok", "status": "ready", "story": story["id"],
              "body": "## Passos\n\n1. x\n\n## Resultado esperado\n\nok\n"},
    ).json()
    execution = client.post(
        "/api/v1/executions", json={"name": "Reg", "testcase_ids": [ct["id"]]}
    ).json()
    client.post(
        f"/api/v1/executions/{execution['id']}/results/{ct['id']}/status",
        json={"status": "passed"},
    )
    summary = client.get("/api/v1/metrics/summary").json()
    assert summary["pass_rate"]["numerator"] == 1
    matrix = client.get("/api/v1/metrics/traceability").json()
    assert matrix["epics"][0]["stories"][0]["last_status"] == "passed"


def test_configure_provider_via_put_keys_go_to_keyring_not_yaml(client):
    resp = client.put(
        "/api/v1/ai/providers",
        json={
            "default_provider": "lmstudio",
            "providers": [
                {"name": "lmstudio", "kind": "openai_compatible",
                 "base_url": "http://localhost:1234/v1", "model": "qwen"},
            ],
            "keys": {"lmstudio": "chave-secreta-xyz"},
        },
    )
    assert resp.status_code == 200
    out = resp.json()
    assert out["default_provider"] == "lmstudio"
    assert out["providers"][0]["key_configured"] is True
    assert "chave-secreta-xyz" not in resp.text
    # a chave NUNCA vai para o arbites.yaml
    ws = client.ws
    assert "chave-secreta-xyz" not in ws.config_path.read_text(encoding="utf-8")
