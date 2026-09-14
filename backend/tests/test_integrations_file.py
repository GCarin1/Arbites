"""Intercâmbio por arquivo — CSV e Cucumber JSON (change 0148, ADR 0015).

Este adaptador é o SEGUNDO, e é por isso que ele importa mais do que parece:
não existe abstração antes da segunda implementação. Uma porta construída com
uma ferramenta na mão sai com o formato daquela ferramenta — estes testes
exercitam a mesma porta por um transporte que não tem API, nem credencial,
nem rede.
"""

import json

import pytest
from conftest import login_admin

from arbites.integrations_file import (
    COLUNAS_CASO,
    ArquivoErro,
    exportar_casos,
    ler_csv,
    ler_cucumber,
)

CORPO = "## Passos\n\n1. abrir\n\n## Resultado esperado\n\nabre\n"


def _csv(linhas: list[dict]) -> str:
    cabecalho = ",".join(COLUNAS_CASO)
    corpo = []
    for linha in linhas:
        corpo.append(",".join(
            '"%s"' % str(linha.get(c, "")).replace('"', '""') for c in COLUNAS_CASO
        ))
    return cabecalho + "\n" + "\n".join(corpo) + "\n"


# -- ida e volta -------------------------------------------------------------


def test_exportar_e_reimportar_o_mesmo_arquivo_nao_duplica(client):
    """A idempotência vem do VÍNCULO (change 0145), não da ordem das linhas:
    reimportar encontra o mesmo `external_id` e atualiza no lugar."""
    conteudo = _csv([
        {"external_id": "TC-EXT-1", "title": "Login válido", "body": CORPO},
        {"external_id": "TC-EXT-2", "title": "Login inválido", "body": CORPO},
    ])

    primeira = client.post("/api/v1/integrations/file/testcases",
                           json={"content": conteudo}).json()
    assert len(primeira["created"]) == 2
    assert primeira["updated"] == []

    # exporta o que entrou e reimporta EXATAMENTE isso
    exportado = client.get("/api/v1/integrations/file/testcases").text
    segunda = client.post("/api/v1/integrations/file/testcases",
                          json={"content": exportado}).json()
    assert segunda["created"] == []
    assert sorted(segunda["updated"]) == sorted(primeira["created"])

    casos = client.get("/api/v1/testcases").json()
    assert len([c for c in casos if c["title"].startswith("Login")]) == 2


def test_o_exportado_carrega_a_identidade_externa(client):
    client.post("/api/v1/integrations/file/testcases", json={
        "content": _csv([{"external_id": "CARD-9", "title": "Com id externo",
                          "body": CORPO}])})

    exportado = client.get("/api/v1/integrations/file/testcases").text
    assert "CARD-9" in exportado
    # e o cabeçalho é o formato neutro, não o de uma ferramenta específica
    assert exportado.splitlines()[0] == ",".join(COLUNAS_CASO)


# -- o que falha, e como -----------------------------------------------------


def test_coluna_faltando_falha_dizendo_qual(client):
    """Importar 40 de 50 linhas e calar sobre as 10 é pior do que não
    importar: o buraco não aparece."""
    sem_titulo = "external_id,body\nTC-1,corpo\n"
    r = client.post("/api/v1/integrations/file/testcases",
                    json={"content": sem_titulo})
    assert r.status_code == 422
    erro = r.json()["error"]
    assert erro["code"] == "missing_column"
    assert "`title`" in erro["message"]
    # e diz o que ENCONTROU, para quem manda o arquivo saber o que corrigir
    assert "external_id" in erro["message"]


def test_cabecalho_validado_antes_de_qualquer_linha(client):
    antes = len(client.get("/api/v1/testcases").json())
    client.post("/api/v1/integrations/file/testcases",
                json={"content": "external_id,body\nTC-1,x\n"})
    assert len(client.get("/api/v1/testcases").json()) == antes


def test_linha_sem_titulo_e_recusada_com_o_numero_da_linha(client):
    conteudo = _csv([
        {"external_id": "TC-1", "title": "Tem título", "body": CORPO},
        {"external_id": "TC-2", "title": "", "body": CORPO},
    ])
    r = client.post("/api/v1/integrations/file/testcases/preview",
                    json={"content": conteudo})
    assert r.status_code == 422
    assert "linha 3" in r.json()["error"]["message"]


def test_csv_vazio_nao_passa_por_arquivo_valido():
    with pytest.raises(ArquivoErro) as e:
        ler_csv("", ["title"])
    assert e.value.code == "empty_csv"


# -- a prévia diz o que fica de fora -----------------------------------------


def test_previa_declara_que_evidencia_sai_como_caminho(client):
    plano = client.post("/api/v1/integrations/file/testcases/preview", json={
        "content": _csv([{"external_id": "TC-1", "title": "Qualquer",
                          "body": CORPO}])}).json()
    aviso = " ".join(plano["warnings"])
    assert "CAMINHO" in aviso
    assert "não como anexo" in aviso or "não carrega o binário" in aviso


def test_previa_separa_criar_de_atualizar(client):
    client.post("/api/v1/integrations/file/testcases", json={
        "content": _csv([{"external_id": "TC-1", "title": "Já existe",
                          "body": CORPO}])})

    plano = client.post("/api/v1/integrations/file/testcases/preview", json={
        "content": _csv([
            {"external_id": "TC-1", "title": "Já existe (novo título)"},
            {"external_id": "TC-2", "title": "Esse é novo"},
        ])}).json()
    assert [c["external_id"] for c in plano["create"]] == ["TC-2"]
    assert [u["external_id"] for u in plano["update"]] == ["TC-1"]


def test_linha_sem_identidade_externa_avisa_que_a_volta_duplica(client):
    """Sem `external_id` não há como reconhecer o que já entrou — e isso é
    dito ANTES, não descoberto na segunda importação."""
    plano = client.post("/api/v1/integrations/file/testcases/preview", json={
        "content": _csv([{"title": "Sem identidade", "body": CORPO}])}).json()
    assert plano["without_identity"]
    assert any("reimportar" in a for a in plano["warnings"])


def test_external_id_repetido_no_mesmo_arquivo_e_ignorado_e_dito(client):
    """Duas linhas para o mesmo item tornam indecidível qual vale."""
    plano = client.post("/api/v1/integrations/file/testcases/preview", json={
        "content": _csv([
            {"external_id": "TC-DUP", "title": "Primeira"},
            {"external_id": "TC-DUP", "title": "Segunda"},
        ])}).json()
    assert len(plano["skipped_duplicates"]) == 1
    assert plano["skipped_duplicates"][0]["first_line"] == 2

    feito = client.post("/api/v1/integrations/file/testcases", json={
        "content": _csv([
            {"external_id": "TC-DUP", "title": "Primeira", "body": CORPO},
            {"external_id": "TC-DUP", "title": "Segunda", "body": CORPO},
        ])}).json()
    assert len(feito["created"]) == 1


def test_previa_nomeia_o_que_o_adaptador_nao_representa(client):
    plano = client.post("/api/v1/integrations/file/testcases/preview", json={
        "content": _csv([{"external_id": "TC-1", "title": "X"}])}).json()
    # o adaptador de arquivo representa tudo, só que sob formas diferentes —
    # e a lista existe para o dia em que um adaptador não representar
    assert "not_represented" in plano


# -- resultados e Cucumber ---------------------------------------------------


def test_exportar_resultados_leva_o_caminho_da_evidencia_nao_o_binario(client):
    ct = client.post("/api/v1/testcases",
                     json={"title": "Com print", "body": CORPO}).json()["id"]
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo exportado", "owner": "qa", "testcase_ids": [ct]}).json()["id"]
    client.put(f"/api/v1/executions/{execucao}/results/{ct}",
               json={"status": "failed"})
    client.post(
        f"/api/v1/executions/{execucao}/results/{ct}/evidences",
        files={"file": ("falha.png", b"\x89PNG\r\n\x1a\nbin", "image/png")},
    )

    csv_texto = client.get("/api/v1/integrations/file/results",
                           params={"execution": execucao}).text
    assert "falha.png" in csv_texto          # o caminho está lá
    assert "\x89PNG" not in csv_texto        # o binário, não


def test_cucumber_liga_cenario_a_caso_pela_tag():
    cenarios = ler_cucumber(json.dumps([{
        "name": "Login",
        "elements": [
            {"name": "com senha válida", "tags": [{"name": "@CT-0007"}, {"name": "@smoke"}],
             "steps": [{"result": {"status": "passed"}}]},
            {"name": "sem tag nenhuma", "tags": [],
             "steps": [{"result": {"status": "failed"}}]},
        ],
    }]))
    assert cenarios[0]["testcase_id"] == "CT-0007"
    assert cenarios[0]["status"] == "passed"
    assert cenarios[1]["testcase_id"] is None
    assert cenarios[1]["status"] == "failed"


def test_cucumber_sem_tag_vira_aviso_e_nao_silencio(client):
    conteudo = json.dumps([{
        "name": "Checkout",
        "elements": [{"name": "orfão", "tags": [], "steps": []}],
    }])
    plano = client.post("/api/v1/integrations/file/cucumber/preview",
                        json={"content": conteudo}).json()
    assert plano["unmatched"]
    assert any("@CT-" in a for a in plano["warnings"])


def test_cucumber_de_formato_errado_e_recusado(client):
    r = client.post("/api/v1/integrations/file/cucumber/preview",
                    json={"content": '{"nao": "e uma lista"}'})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_cucumber"

    r2 = client.post("/api/v1/integrations/file/cucumber/preview",
                     json={"content": "isto não é json"})
    assert r2.json()["error"]["code"] == "invalid_json"
