"""Manifesto v2: rótulos e achados estruturados (change 0175).

Duas lacunas que só aparecem num projeto de verdade:

- o repositório onde o workflow mora NÃO é o que está sob teste. Num projeto
  de micro-frontends o mesmo repositório de testes valida vários componentes,
  e a taxa de sucesso global vira a média de coisas diferentes;
- `violacoes_axe: 14` diz que piorou, não diz o quê. Sem regra, gravidade e
  critério da WCAG não há como priorizar.
"""

import json

import pytest

from arbites.ci_axe import ler_axe, normalizar_achados
from arbites.ci_ingest import (
    VERSOES_ACEITAS, IngestError, extrair_achados, ler_manifesto,
    normalizar_rotulos,
)


def _axe(violacoes, url="https://app/carteira"):
    return json.dumps({"url": url, "violations": violacoes}).encode()


CONTRASTE = {"id": "color-contrast", "impact": "serious",
             "tags": ["cat.color", "wcag2aa", "wcag143"],
             "help": "Contraste insuficiente", "helpUrl": "https://x",
             "nodes": [{}, {}, {}]}


# -- leitor do axe -----------------------------------------------------------

def test_o_criterio_wcag_sai_da_tag_do_axe():
    """`wcag143` → 1.4.3: é a única fonte do número, e sem ele o achado não
    liga na norma que o time cobra."""
    achado = ler_axe(_axe([CONTRASTE]))[0]
    assert achado["wcag"] == "1.4.3"
    assert achado["level"] == "AA"
    assert achado["rule"] == "color-contrast"
    assert achado["impact"] == "serious"


def test_o_numero_e_de_elementos_nao_de_regras():
    """Três nós violando a mesma regra são três lugares para consertar."""
    assert ler_axe(_axe([CONTRASTE]))[0]["count"] == 3


def test_varias_rotas_num_arquivo_so():
    """Uma varredura de micro-frontends produz uma entrada por rota."""
    doc = json.dumps([
        {"url": "https://app/a", "violations": [CONTRASTE]},
        {"url": "https://app/b", "violations": [CONTRASTE]},
    ]).encode()
    achados = ler_axe(doc)
    assert len(achados) == 2
    assert {a["page"] for a in achados} == {"https://app/a", "https://app/b"}


def test_resultado_embrulhado_ainda_e_lido():
    doc = json.dumps({"results": {"url": "u", "violations": [CONTRASTE]}}).encode()
    assert len(ler_axe(doc)) == 1


def test_impacto_fora_da_escala_vira_desconhecido_e_nao_some():
    """Sumir seria mentir na soma por gravidade."""
    esquisito = {**CONTRASTE, "impact": "catastrofico"}
    assert ler_axe(_axe([esquisito]))[0]["impact"] == "unknown"


def test_json_quebrado_nao_derruba_a_ingestao():
    """Artifact ruim é problema daquele run, não da série."""
    assert ler_axe(b"nao e json") == []
    assert ler_axe(json.dumps({"violations": "errado"}).encode()) == []


def test_achado_declarado_no_manifesto_tem_a_mesma_forma():
    """Duas formas para a mesma coisa viram dois caminhos de agregação."""
    achado = normalizar_achados([{
        "category": "performance", "rule": "bundle-size", "impact": "moderate",
        "count": 4, "page": "/carteira"}])[0]
    assert set(achado) == set(ler_axe(_axe([CONTRASTE]))[0])


# -- rótulos -----------------------------------------------------------------

def test_rotulos_sao_chave_livre():
    """A topologia é de quem instala: fixar componente/ambiente no código só
    obrigaria a contorná-los depois."""
    rotulos = normalizar_rotulos({"labels": {
        "componente": "carteira-mfe", "ambiente": " hml ", "squad": "renda-variavel"}})
    assert rotulos == {"componente": "carteira-mfe", "ambiente": "hml",
                       "squad": "renda-variavel"}


def test_rotulo_vazio_ou_nulo_nao_entra():
    assert normalizar_rotulos({"labels": {"a": "", "b": None, "c": "x"}}) == {"c": "x"}


def test_labels_de_tipo_errado_nao_quebra():
    assert normalizar_rotulos({"labels": ["nao", "e", "dict"]}) == {}


# -- manifesto ---------------------------------------------------------------

@pytest.mark.parametrize("versao", VERSOES_ACEITAS)
def test_as_duas_versoes_do_manifesto_sao_lidas(versao):
    """A v1 não pode parar de valer porque o formato cresceu."""
    arquivos = {"arbites.json": json.dumps({"version": versao}).encode()}
    manifesto, aviso = ler_manifesto(arquivos)
    assert aviso is None and manifesto["version"] == versao


def test_versao_desconhecida_e_recusada_dizendo_o_que_se_le():
    arquivos = {"arbites.json": json.dumps({"version": 99}).encode()}
    with pytest.raises(IngestError) as exc:
        ler_manifesto(arquivos)
    assert exc.value.code == "manifest_version"
    assert "1, 2" in str(exc.value)


def test_o_anexo_axe_e_lido_sem_o_pipeline_reescrever_nada():
    manifesto = {"version": 2, "attachments": [{"kind": "axe", "path": "axe.json"}]}
    achados = extrair_achados(manifesto, {"axe.json": _axe([CONTRASTE])})
    assert achados[0]["rule"] == "color-contrast"


def test_axe_por_convencao_quando_o_manifesto_nao_declara():
    achados = extrair_achados({"version": 2}, {"relatorio-a11y.json": _axe([CONTRASTE])})
    assert len(achados) == 1


def test_manifesto_e_axe_somam_em_vez_de_um_anular_o_outro():
    manifesto = {"version": 2,
                 "findings": [{"rule": "bundle-size", "category": "performance"}],
                 "attachments": [{"kind": "axe", "path": "axe.json"}]}
    achados = extrair_achados(manifesto, {"axe.json": _axe([CONTRASTE])})
    assert {a["rule"] for a in achados} == {"bundle-size", "color-contrast"}
