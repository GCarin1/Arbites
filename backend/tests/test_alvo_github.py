"""O bloco `github` do alvo, ida e volta pela tela (change 0172).

`AutomationTargetIn` não tinha campo `github`, e `PUT /targets` reserializa o
alvo inteiro a partir do modelo: salvar pela tela APAGAVA o bloco escrito à
mão no `arbites.yaml`. Como também não havia campo na tela, disparar no
GitHub respondia 422 e não havia lugar nenhum onde resolver.
"""

import pytest
from conftest import logged_in_client


def _alvo(tmp_path, github=None):
    alvo = {"name": "Teste", "kind": "behave", "local_path": str(tmp_path)}
    if github is not None:
        alvo["github"] = github
    return alvo


def test_o_bloco_github_sobrevive_a_um_salvamento_pela_tela(ws, tmp_path):
    """O defeito central: ida e volta sem perder o que foi configurado."""
    gh = {"repo": "org/repositorio", "workflow": "e2e.yml", "ref": "develop"}
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/targets", json={"targets": [_alvo(tmp_path, gh)]})
        assert r.status_code == 200, r.text
        assert r.json()[0]["github"] == gh
        # e continua no YAML, que é a fonte de verdade
        salvo = client.ws.config()["automation_targets"][0]
        assert salvo["github"]["repo"] == "org/repositorio"
        assert salvo["github"]["workflow"] == "e2e.yml"

        # salvar DE NOVO com o que a tela devolveu não apaga nada
        de_volta = client.get("/api/v1/targets").json()
        r2 = client.put("/api/v1/targets", json={"targets": [{
            "name": de_volta[0]["name"], "kind": de_volta[0]["kind"],
            "local_path": de_volta[0]["local_path"],
            "github": de_volta[0]["github"],
        }]})
        assert r2.status_code == 200, r2.text
        assert r2.json()[0]["github"] == gh


def test_bloco_pela_metade_nao_e_gravado(ws, tmp_path):
    """Um `github:` com repo e sem workflow é pior que nenhum: o erro do
    disparo acusaria falta de configuração com o bloco na cara de quem olha."""
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/targets", json={
            "targets": [_alvo(tmp_path, {"repo": "org/repo", "workflow": ""})]})
        assert r.status_code == 200, r.text
        assert r.json()[0]["github"] is None
        assert "github" not in client.ws.config()["automation_targets"][0]


def test_alvo_sem_github_continua_valido(ws, tmp_path):
    """Execução local não precisa de GitHub nenhum."""
    with logged_in_client(ws) as client:
        r = client.put("/api/v1/targets", json={"targets": [_alvo(tmp_path)]})
        assert r.status_code == 200, r.text
        assert r.json()[0]["github"] is None


def test_o_422_do_disparo_diz_onde_resolver(ws, tmp_path):
    from arbites.ci import CIError, CIManager

    with logged_in_client(ws) as client:
        client.put("/api/v1/targets", json={"targets": [_alvo(tmp_path)]})
        gerente = CIManager(client.ws, None, None, None)
        with pytest.raises(CIError) as exc:
            gerente._target("Teste")
        assert exc.value.status == 422
        assert "Automação → Configurar" in str(exc.value)
