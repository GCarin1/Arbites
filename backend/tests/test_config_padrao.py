"""O `arbites.yaml` que nasce na primeira execução (change 0167).

O defeito: o arquivo era um `yaml.safe_dump` do dicionário de defaults — cinco
chaves sem uma linha de explicação — enquanto o produto LIA onze. Seis
funcionalidades existiam e ninguém descobria. Configuração que não aparece é
configuração que não existe.
"""

import re
from pathlib import Path

import pytest
import yaml

from arbites.workspace import CONFIG_TEMPLATE, DEFAULT_CONFIG, Workspace

RAIZ = Path(__file__).resolve().parents[2]


def test_o_template_e_o_default_nao_divergem():
    """A guarda do desenho: o arquivo escrito vem de um template com
    comentários, e o código lê de um dicionário. Dois lugares que dizem a
    mesma coisa divergem sozinhos — este teste é o que impede."""
    assert yaml.safe_load(CONFIG_TEMPLATE) == DEFAULT_CONFIG


def test_o_arquivo_gerado_cobre_tudo_que_o_produto_le():
    """Enumera as chaves realmente consultadas no código e exige que cada uma
    apareça no arquivo que a pessoa recebe."""
    lidas = set()
    for arquivo in (RAIZ / "backend" / "arbites").glob("*.py"):
        texto = arquivo.read_text(encoding="utf-8")
        lidas.update(re.findall(r'config\(\)\.get\("([a-z_]+)"', texto))
        lidas.update(re.findall(r'cfg\.get\("([a-z_]+)"', texto))
    # `cfg` também é usado para sub-blocos; só interessam os de topo
    do_arquivo = set(yaml.safe_load(CONFIG_TEMPLATE))
    faltando = {k for k in lidas if k in {
        "ai", "audit", "automation_targets", "ci_monitoring", "health_score",
        "metric_thresholds", "observability", "requirements", "risk_repos",
        "squads", "workspace",
    }} - do_arquivo
    assert not faltando, f"o produto lê mas o arquivo não mostra: {faltando}"


def test_o_arquivo_nasce_comentado_e_nao_como_dump_mudo(tmp_path):
    ws = Workspace(tmp_path / "w")
    ws.ensure()
    texto = ws.config_path.read_text(encoding="utf-8")

    assert texto.count("#") > 30, "o arquivo precisa se explicar"
    # e as seis que estavam invisíveis agora aparecem
    for bloco in ("audit:", "requirements:", "metric_thresholds:",
                  "health_score:", "ci_monitoring:", "squads:"):
        assert bloco in texto


def test_o_arquivo_gerado_avisa_que_segredo_nao_entra_nele(tmp_path):
    """É a confusão mais provável de quem configura: o YAML fica DENTRO do
    workspace, que é versionável."""
    ws = Workspace(tmp_path / "w")
    ws.ensure()
    texto = ws.config_path.read_text(encoding="utf-8")
    assert "SEGREDO NÃO ENTRA AQUI" in texto
    assert ".env" in texto


def test_o_arquivo_gerado_e_yaml_valido_e_carrega_como_config(tmp_path):
    ws = Workspace(tmp_path / "w")
    ws.ensure()
    assert ws.config() == DEFAULT_CONFIG


def test_ensure_nao_sobrescreve_um_arquivo_existente(tmp_path):
    ws = Workspace(tmp_path / "w")
    ws.ensure()
    ws.config_path.write_text("workspace:\n  name: Meu\n", encoding="utf-8")
    ws.ensure()
    assert ws.config()["workspace"]["name"] == "Meu"


# -- o .env de exemplo -------------------------------------------------------


def test_env_de_exemplo_cobre_as_variaveis_que_o_produto_le():
    exemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    for variavel in ("ARBITES_ADMIN_EMAIL", "ARBITES_ADMIN_PASSWORD",
                     "ARBITES_SIGNUP", "ARBITES_GITHUB_TOKEN",
                     "ARBITES_WORKSPACE", "ARBITES_FRONTEND_DIST",
                     "ARBITES_AUTH"):
        assert variavel in exemplo, f"{variavel} não está no .env.example"


def test_env_de_exemplo_diz_que_vale_fora_do_container():
    """Era a causa raiz da change 0165: quem lê o `.env` no Docker é o
    Compose, e o exemplo dizia "variáveis do docker-compose"."""
    exemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    assert "sem Docker" in exemplo
    assert "python -m arbites serve" in exemplo


def test_env_de_exemplo_nao_traz_segredo_de_verdade():
    exemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    assert "github_pat_..." in exemplo  # placeholder, não um token real
    assert not re.search(r"github_pat_[A-Za-z0-9_]{20,}", exemplo)
