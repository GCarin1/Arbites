"""Robustez da conversão estruturada em modelos locais ≤ 9B (doc §1.1).

O modelo costuma vazar raciocínio e reconstruir o JSON Schema antes de emitir
os dados; `complete()` deve ignorar isso e escolher o objeto que valida no
schema. Além disso usa `response_format: json_object`, com fallback quando o
servidor não o suporta.
"""

import json

import httpx
import pytest

from arbites.ai import (
    AIKeyStore,
    AIProviderError,
    ImportConversion,
    OpenAICompatible,
    _example_from_model,
    _salvage_import,
    convert_import,
)

DATA = {
    "folder": "login",
    "testcases": [
        {
            "title": "CT01 login válido",
            "pre_condicoes": ["usuário cadastrado"],
            "passos": ["abrir login", "informar credenciais"],
            "resultado_esperado": "dashboard exibido",
        }
    ],
}


class FakeKeys(AIKeyStore):
    def __init__(self):
        self._keys = {}

    def set(self, provider, key):
        self._keys[provider] = key

    def get(self, provider):
        return self._keys.get(provider)


def _provider(handler):
    return OpenAICompatible(
        "local", "gemma-2-9b", FakeKeys(),
        base_url="http://localhost:1234/v1",
        transport=httpx.MockTransport(handler),
    )


def _chat_response(content: str, reasoning: str | None = None) -> httpx.Response:
    message: dict = {"content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return httpx.Response(200, json={"choices": [{"message": message}]})


def test_example_from_model_is_compact_not_json_schema():
    ex = _example_from_model(ImportConversion)
    # exemplo concreto e preenchível — sem artefatos de JSON Schema.
    assert set(ex) == {"folder", "testcases"}
    assert "$defs" not in ex and "properties" not in ex
    assert ex["folder"] == "importados"  # default textual do campo
    tc = ex["testcases"][0]
    assert isinstance(tc, dict) and "title" in tc and "resultado_esperado" in tc


def test_extracts_data_ignoring_reasoning_and_schema_reconstruction():
    # o modelo raciocina, reconstrói o schema e SÓ ENTÃO emite os dados.
    noisy = (
        "<think>Preciso analisar o schema. properties: folder, testcases...</think>\n"
        'Schema plan: {"$defs": {"GeneratedTestcase": {"required": ["title"]}}}\n'
        "Final Plan: vou gerar os casos.\n"
        f"{json.dumps(DATA, ensure_ascii=False)}\n"
        "Pronto."
    )
    result = _provider(lambda req: _chat_response(noisy)).complete(
        "sys", "user", ImportConversion
    )
    assert isinstance(result, ImportConversion)
    assert result.folder == "login"
    assert result.testcases[0].title == "CT01 login válido"


def test_extracts_data_from_fenced_block_among_prose():
    fenced = (
        "Claro! Aqui estão os casos convertidos:\n\n"
        f"```json\n{json.dumps(DATA, ensure_ascii=False)}\n```\n"
        "Espero ter ajudado."
    )
    result = convert_import(_provider(lambda req: _chat_response(fenced)), "f.txt", "x")
    assert result.testcases[0].resultado_esperado == "dashboard exibido"


def test_json_mode_sent_and_falls_back_when_unsupported():
    seen = {"with_rf": 0, "without_rf": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        payload = json.loads(req.content)
        if "response_format" in payload:
            seen["with_rf"] += 1
            return httpx.Response(400, text="response_format not supported")
        seen["without_rf"] += 1
        return _chat_response(json.dumps(DATA, ensure_ascii=False))

    result = convert_import(_provider(handler), "f.txt", "x")
    assert isinstance(result, ImportConversion)
    assert seen["with_rf"] == 1 and seen["without_rf"] == 1  # tentou json_mode e caiu no fallback


def test_reasoning_content_used_when_content_empty():
    # glm-4.7-flash: content vazio, JSON acabou saindo no reasoning_content.
    reasoning = (
        "Vou analisar o schema e extrair os casos.\n"
        f"Resultado: {json.dumps(DATA, ensure_ascii=False)}"
    )
    result = _provider(
        lambda req: _chat_response("", reasoning=reasoning)
    ).complete("sys", "user", ImportConversion)
    assert isinstance(result, ImportConversion)
    assert result.testcases[0].title == "CT01 login válido"


def test_salvages_complete_testcases_from_truncated_output():
    # geração cortada por timeout: objeto externo não fecha, CT03 vem pela metade.
    truncated = (
        '{"folder": "google_search", "testcases": [\n'
        '  {"title": "CT01", "passos": ["p1"], "resultado_esperado": "r1"},\n'
        '  {"title": "CT02", "passos": ["p2"], "resultado_esperado": "r2"},\n'
        '  {"title": "CT03", "passos": ["p3"], "pre_condicoes": ["o usuário acessa a página inicial'
    )
    result = _provider(lambda req: _chat_response(truncated)).complete(
        "sys", "user", ImportConversion, salvage=_salvage_import,
    )
    assert isinstance(result, ImportConversion)
    # recupera os dois CTs inteiros e a pasta do cabeçalho, descarta o truncado.
    assert [tc.title for tc in result.testcases] == ["CT01", "CT02"]
    assert result.folder == "google_search"


def test_convert_import_salvages_end_to_end():
    from arbites.ai import convert_import

    truncated = (
        '{"folder": "login", "testcases": [\n'
        '  {"title": "CT01 ok", "pre_condicoes": ["cadastrado"], "passos": ["abrir"], "resultado_esperado": "dashboard"},\n'
        '  {"title": "CT02 inv'
    )
    result = convert_import(
        _provider(lambda req: _chat_response(truncated)), "casos.txt", "x"
    )
    assert result.folder == "login"
    assert [tc.title for tc in result.testcases] == ["CT01 ok"]


def test_no_valid_json_raises_clear_error():
    prov = _provider(lambda req: _chat_response("Desculpe, não consegui."))
    with pytest.raises(AIProviderError) as exc:
        prov.complete("sys", "user", ImportConversion)
    assert exc.value.code in ("invalid_output", "schema_mismatch")
