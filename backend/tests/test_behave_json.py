"""parse_behave_json — prefixo de CT configurável (mudança 0067).

O adapter do Cucumber JSON casava a tag do cenário contra `CT-\\d+`
hardcoded; um workspace com `id_prefixes.testcase` customizado (ex.: "TC")
faria os resultados do Behave sumirem silenciosamente na hora de casar com
a execution — nem o run local nem a coleta de CI encontrariam o cenário.
"""

import json

from arbites.behave_json import parse_behave_json


def _cucumber_json(tag: str, status: str = "passed") -> bytes:
    return json.dumps(
        [
            {
                "name": "Feature genérica",
                "elements": [
                    {
                        "type": "scenario",
                        "name": "Cenário de exemplo",
                        "tags": [tag],
                        "steps": [
                            {"result": {"status": status, "duration": 0.5}},
                        ],
                    }
                ],
            }
        ]
    ).encode("utf-8")


def test_parse_behave_json_default_prefix_matches_ct():
    results = parse_behave_json(_cucumber_json("@CT-0001"))
    assert list(results.keys()) == ["CT-0001"]


def test_parse_behave_json_custom_prefix_matches_configured_id():
    results = parse_behave_json(_cucumber_json("@TC-0001"), ct_prefix="TC")
    assert list(results.keys()) == ["TC-0001"]


def test_parse_behave_json_custom_prefix_ignores_unrelated_tag():
    # com prefixo customizado "TC", uma tag @CT-0001 não é mais reconhecida
    # (evita falso positivo se o workspace mudou de prefixo)
    results = parse_behave_json(_cucumber_json("@CT-0001"), ct_prefix="TC")
    assert results == {}


def test_parse_behave_json_scenario_without_any_ct_tag_is_skipped_not_crashed():
    results = parse_behave_json(_cucumber_json("@smoke"))
    assert results == {}
