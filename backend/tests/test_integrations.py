"""Identidade externa (change 0145, ADR 0015).

O alicerce de toda sincronia: saber o que daqui já está lá. Sem isso o agente
recria o que já criou — em conversa nova, sem memória, isso acontece na
primeira semana.
"""

import frontmatter

from arbites import integrations as integ
from arbites.indexer import reindex_full

CORPO = "## Passos\n\n1. Abrir a tela\n\n## Resultado esperado\n\nok\n"


def _caso(client, titulo="Login com senha valida"):
    return client.post(
        "/api/v1/testcases", json={"title": titulo, "body": CORPO}
    ).json()


def _ligar(client, ct_id, system="businessmap", remote="CARD-4821", **extra):
    r = client.put(
        f"/api/v1/integrations/links/testcase/{ct_id}",
        json={"system": system, "id": remote, **extra},
    )
    assert r.status_code == 200, r.text
    return r.json()


# -- o vínculo mora no arquivo ----------------------------------------------


def test_vinculo_sobrevive_a_um_reindex_completo(client, ws):
    """O índice é descartável (ADR 0001); o vínculo não pode morrer com ele.

    Se morresse, um reindex apagaria a memória do que já foi sincronizado — e
    a próxima sincronia recriaria no sistema oficial tudo o que já existe lá.
    """
    ct = _caso(client)
    _ligar(client, ct["id"])

    # some com o índice inteiro e reconstrói do zero
    conn = client.app.state.conn
    for tabela in ("testcases", "requirements"):
        conn.execute(f"DELETE FROM {tabela}")
    conn.commit()
    reindex_full(client.app.state.ws, conn)

    links = client.get("/api/v1/integrations/links").json()["links"]
    meu = [x for x in links if x["entity_id"] == ct["id"]]
    assert meu and meu[0]["remote_id"] == "CARD-4821"


def test_vinculo_esta_no_frontmatter_e_nao_so_no_indice(client, ws):
    ct = _caso(client)
    _ligar(client, ct["id"])
    caminho = client.app.state.conn.execute(
        "SELECT path FROM testcases WHERE id = ?", (ct["id"],)
    ).fetchone()["path"]
    meta = frontmatter.load(str(client.app.state.ws.root / caminho)).metadata
    assert meta["external"][0]["system"] == "businessmap"
    assert meta["external"][0]["id"] == "CARD-4821"
    assert meta["external"][0]["synced_hash"], "sem hash não há detecção de conflito"


def test_dois_sistemas_no_mesmo_artefato_convivem(client):
    """Migração corporativa tem os dois vivos ao mesmo tempo: perder o antigo
    enquanto o novo nasce é perder o rastro quando ele mais importa."""
    ct = _caso(client)
    _ligar(client, ct["id"], system="xray", remote="QA-100")
    saida = _ligar(client, ct["id"], system="businessmap", remote="CARD-1")
    assert {v["system"] for v in saida["external"]} == {"xray", "businessmap"}

    so_xray = client.get("/api/v1/integrations/links?system=xray").json()["links"]
    assert {x["remote_id"] for x in so_xray if x["entity_id"] == ct["id"]} == {"QA-100"}


def test_desligar_um_sistema_preserva_o_outro(client):
    ct = _caso(client)
    _ligar(client, ct["id"], system="xray", remote="QA-100")
    _ligar(client, ct["id"], system="businessmap", remote="CARD-1")
    assert client.delete(
        f"/api/v1/integrations/links/testcase/{ct['id']}/xray"
    ).status_code == 204
    restantes = client.get(
        f"/api/v1/integrations/links?system=businessmap"
    ).json()["links"]
    assert any(x["entity_id"] == ct["id"] for x in restantes)


# -- pendência e conflito ----------------------------------------------------


def test_editar_depois_de_sincronizar_deixa_pendente(client):
    """`synced_hash` é o que permite responder "mudou?" — data não responde."""
    ct = _caso(client)
    _ligar(client, ct["id"])
    assert _estado(client, ct["id"]) == "in_sync"

    client.put(
        f"/api/v1/testcases/{ct['id']}",
        json={"title": ct["title"], "body": CORPO + "\n2. Passo novo\n"},
    )
    assert _estado(client, ct["id"]) == "local_changed"

    pendentes = client.get(
        "/api/v1/integrations/links?state=local_changed"
    ).json()["links"]
    assert any(x["entity_id"] == ct["id"] for x in pendentes)

    # sincronizar de novo tira da lista
    _ligar(client, ct["id"])
    assert _estado(client, ct["id"]) == "in_sync"


def _estado(client, ct_id):
    for x in client.get("/api/v1/integrations/links").json()["links"]:
        if x["entity_id"] == ct_id and x["system"]:
            return x["state"]
    return None


def test_artefato_nunca_ligado_aparece_como_never_synced(client):
    ct = _caso(client, "Ainda sem vínculo")
    links = client.get("/api/v1/integrations/links").json()["links"]
    meu = [x for x in links if x["entity_id"] == ct["id"]][0]
    assert meu["state"] == "never_synced" and meu["system"] is None


def test_filtrar_por_never_synced_devolve_quem_nunca_foi(client):
    """É a pergunta "o que ainda não foi para lá?" — e ela precisa responder.

    Sem isto o filtro só enxergava quem JÁ tinha vínculo, que é exatamente o
    conjunto complementar do que se procura.
    """
    ligado = _caso(client, "Já ligado")
    _ligar(client, ligado["id"])
    solto = _caso(client, "Nunca ligado")

    nunca = client.get(
        "/api/v1/integrations/links?state=never_synced"
    ).json()["links"]
    ids = {x["entity_id"] for x in nunca}
    assert solto["id"] in ids
    assert ligado["id"] not in ids


def test_mudanca_dos_dois_lados_e_conflito_e_ninguem_e_sobrescrito():
    """A regra da ADR 0015: o sistema NÃO decide. Último-que-escreve-vence é
    perda silenciosa, e numa ferramenta de rastreabilidade é o pior defeito."""
    vinculo = {"system": "businessmap", "id": "CARD-1",
               "revision": "17", "synced_hash": "aaa"}
    assert integ.sync_state(vinculo, "aaa", "17") == "in_sync"
    assert integ.sync_state(vinculo, "bbb", "17") == "local_changed"
    assert integ.sync_state(vinculo, "aaa", "18") == "remote_changed"
    assert integ.sync_state(vinculo, "bbb", "18") == "conflict"
    assert integ.sync_state(None, "aaa") == "never_synced"


def test_hash_ignora_o_frontmatter(client):
    """Se o hash incluísse o frontmatter, gravar o vínculo mudaria o hash que
    ele acabou de gravar — o artefato nasceria pendente de si mesmo."""
    ct = _caso(client)
    _ligar(client, ct["id"])
    antes = _estado(client, ct["id"])
    _ligar(client, ct["id"], remote="CARD-OUTRO")  # mexe só no frontmatter
    assert antes == "in_sync" and _estado(client, ct["id"]) == "in_sync"


# -- capacidades declaradas --------------------------------------------------


def test_adaptador_declara_o_que_nao_representa(client):
    """O que a ferramenta não guarda é dito ANTES, não descoberto depois."""
    adaptadores = client.get("/api/v1/integrations/capabilities").json()["adapters"]
    por_sistema = {a["system"]: a for a in adaptadores}

    # o Businessmap é um quadro Kanban: caso de teste vira card, não é nativo
    assert por_sistema["businessmap"]["supports"]["testcase"] == "card"
    # o arquivo carrega o CAMINHO da evidência, não o binário
    assert por_sistema["file"]["supports"]["evidence"] == "path"
    assert por_sistema["xray"]["supports"]["evidence"] == "native"


def test_capacidade_sabe_listar_o_que_fica_de_fora():
    cap = integ.Capabilities("x", "X", testcase="row", result="row")
    assert cap.nao_representa(["testcase", "evidence", "folder"]) == [
        "evidence", "folder"
    ]


def test_so_caso_e_requisito_tem_vinculo(client):
    r = client.put(
        "/api/v1/integrations/links/defect/DF-0001",
        json={"system": "businessmap", "id": "CARD-9"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unlinkable_kind"
