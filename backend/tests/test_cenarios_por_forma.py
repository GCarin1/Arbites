"""O relatório Cucumber reconhecido pela FORMA, não pelo nome (change 0189).

45 execuções ingeridas, centenas de anexos, e a pizza "Cenários por
resultado" vazia. A causa não era dado faltando: era o relatório chamar-se
`cucumber-report.json` enquanto o reconhecimento exigia terminar exatamente
em `cucumber.json` ou `result.json`.

Reconhecer por nome nunca ia funcionar — cada pipeline nomeia do seu jeito e
a lista de nomes prováveis não termina. A forma, sim, está no padrão.
"""

from __future__ import annotations

import json

import pytest

from arbites import ci_ingest
from arbites.indexer import connect


@pytest.fixture
def conn(ws):
    return connect(ws)


def _cucumber(nome_do_cenario: str = "Login válido", status: str = "passed"):
    return json.dumps([{
        "name": "Login",
        "elements": [{
            "name": nome_do_cenario,
            "tags": [{"name": "@CT-0001"}],
            "steps": [{"result": {"status": status}}],
            "status": status,
        }],
    }]).encode("utf-8")


# --- a forma ----------------------------------------------------------------


@pytest.mark.parametrize("nome", [
    "cucumber-report.json",
    "results.json",
    "report-trader.json",
    "saida/cucumber_2026-09-17.json",
    "NOME-QUE-NINGUEM-ADIVINHARIA.json",
])
def test_o_nome_do_arquivo_deixa_de_importar(nome):
    cenarios = ci_ingest.extrair_cenarios({}, {nome: _cucumber()})

    assert [c["scenario"] for c in cenarios] == ["Login válido"]


def test_json_que_nao_e_cucumber_nao_vira_cenario():
    """Reconhecer demais seria trocar um silêncio por uma mentira."""
    axe = json.dumps({"violations": [{"id": "image-alt"}]}).encode()
    pacote = json.dumps({"name": "app", "version": "1.0"}).encode()

    assert ci_ingest.extrair_cenarios({}, {"a.json": axe}) == []
    assert ci_ingest.extrair_cenarios({}, {"package.json": pacote}) == []


def test_lista_de_json_que_nao_tem_elements_nao_conta():
    lista = json.dumps([{"id": 1}, {"id": 2}]).encode()

    assert not ci_ingest.e_relatorio_cucumber(lista)


@pytest.mark.parametrize("bruto", [b"", b"nao e json", b"[", b"{}", b"[]"])
def test_lixo_nao_derruba_o_reconhecimento(bruto):
    assert not ci_ingest.e_relatorio_cucumber(bruto)


def test_json_gigante_nao_e_desserializado_para_descobrir_a_forma():
    """Um `axe.json` de suíte grande passa de 100 MB; abri-lo em toda
    ingestão só para descobrir que não é Cucumber sairia caro."""
    enorme = b"[" + b"0" * (ci_ingest.LIMITE_FORMA + 1)

    assert not ci_ingest.e_relatorio_cucumber(enorme)


def test_arquivo_que_nao_e_json_nem_e_olhado():
    assert not ci_ingest.e_relatorio_cucumber(b"<html><body>relatorio</body>")


# --- o manifesto continua mandando -----------------------------------------


def test_o_manifesto_declarado_vence_a_forma():
    """Quem declara, manda (ADR 0016). A forma é o fallback, não a regra."""
    manifesto = {"attachments": [{"kind": "cucumber", "path": "o-certo.json"}]}
    arquivos = {
        "o-certo.json": _cucumber("Declarado"),
        "outro.json": _cucumber("Descoberto pela forma"),
    }

    cenarios = ci_ingest.extrair_cenarios(manifesto, arquivos)

    assert [c["scenario"] for c in cenarios] == ["Declarado"]


def test_anexo_sem_manifesto_e_classificado_como_cucumber():
    convencao = ci_ingest._por_convencao({"seja-la-o-nome.json": _cucumber()})

    kinds = {a["path"]: a["kind"] for a in convencao["attachments"]}
    assert kinds["seja-la-o-nome.json"] == "cucumber"


def test_result_json_que_nao_e_cucumber_nao_e_chamado_de_cucumber():
    """O nome `result.json` era classificado como relatório mesmo quando não
    era um: um silêncio virava uma mentira."""
    convencao = ci_ingest._por_convencao({"result.json": b'{"ok": true}'})

    kinds = {a["path"]: a["kind"] for a in convencao["attachments"]}
    assert kinds.get("result.json") != "cucumber"


# --- reprocessar do disco ---------------------------------------------------


def _ingerir_um_run(ws, arquivos: dict[str, bytes]):
    run = {
        "key": "github-1", "provider": "github", "repo": "org/testes",
        "workflow": "Regression", "run_id": "1", "conclusion": "success",
        "started_at": "2026-09-01T10:00:00+00:00",
        "ingested_at": "2026-09-01T11:00:00+00:00",
    }
    manifesto, aviso = ci_ingest.ler_manifesto(arquivos)
    return ci_ingest.escrever_run(ws.root, run, manifesto, arquivos, aviso)


def test_reprocessar_reconhece_o_que_a_ingestao_antiga_perdeu(ws, conn):
    """O caso real: os anexos já estão no disco e o reconhecimento melhorou.
    Apagar e rebuscar seriam horas de download para reler arquivo local."""
    gravado = _ingerir_um_run(ws, {"cucumber-report.json": _cucumber()})
    # Simula o documento escrito pela versão anterior, que não reconhecia.
    import frontmatter

    caminho = ws.root / gravado["path"]
    post = frontmatter.load(caminho)
    post.metadata.pop("scenarios", None)
    caminho.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")

    resumo = ci_ingest.reprocessar(ws, conn)

    assert resumo["atualizados"] == ["github-1"]
    assert frontmatter.load(caminho).metadata["scenarios"][0]["scenario"] \
        == "Login válido"


def test_reprocessar_nao_toca_no_que_veio_do_provedor(ws, conn):
    """Reprocessar não é re-ingerir: conclusão, commit e horário vieram do
    GitHub e não estão nos anexos; sobrescrevê-los seria perder informação."""
    import frontmatter

    gravado = _ingerir_um_run(ws, {"r.json": _cucumber()})
    caminho = ws.root / gravado["path"]
    antes = frontmatter.load(caminho).metadata

    ci_ingest.reprocessar(ws, conn)

    depois = frontmatter.load(caminho).metadata
    for campo in ("conclusion", "started_at", "run_id", "repo", "workflow"):
        assert depois[campo] == antes[campo]


def test_reprocessar_duas_vezes_nao_muda_nada_na_segunda(ws, conn):
    _ingerir_um_run(ws, {"r.json": _cucumber()})
    ci_ingest.reprocessar(ws, conn)

    assert ci_ingest.reprocessar(ws, conn)["atualizados"] == []


def test_anexo_que_sumiu_do_disco_nao_e_erro(ws, conn):
    """O documento continua válido sem o anexo; tratar como erro faria uma
    limpeza de retenção parecer corrupção."""
    gravado = _ingerir_um_run(ws, {"r.json": _cucumber()})
    for anexo in gravado["attachments"]:
        (ws.root / anexo["path"]).unlink()

    resumo = ci_ingest.reprocessar(ws, conn)

    assert resumo["erros"] == []
    assert resumo["lidos"] == 1


def test_reprocessar_sem_nada_ingerido_nao_quebra(ws, conn):
    assert ci_ingest.reprocessar(ws, conn) == {
        "lidos": 0, "atualizados": [], "erros": []}
