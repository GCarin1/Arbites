"""Listas de To Do e o vínculo com o afazer (change 0164).

A divisão que manda no desenho: o AFAZER é a nota adesiva (uma coisa a fazer,
com prazo e status); a LISTA é o roteiro (passos que só fazem sentido juntos,
com prazo da lista). A LINHA não tem prazo — quando precisa de um, liga-se a
um afazer. O afazer traz a data, a linha traz o passo.
"""

from datetime import date, timedelta

import pytest
from conftest import login_admin


def _dia(delta: int) -> str:
    return (date.today() + timedelta(days=delta)).isoformat()


def _lista(client, titulo="Preparar release 4.2", due=None) -> dict:
    r = client.post("/api/v1/todolists",
                    json={"title": titulo, "due": due})
    assert r.status_code == 201, r.text
    return r.json()


def _linha(client, list_id, texto, **kw) -> dict:
    r = client.post(f"/api/v1/todolists/{list_id}/items",
                    json={"text": texto, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def _afazer(client, titulo="Um afazer", **kw) -> str:
    return client.post("/api/v1/todos", json={"title": titulo, **kw}).json()["id"]


# -- a lista ----------------------------------------------------------------


def test_lista_nasce_com_id_proprio_e_vira_arquivo(client):
    lista = _lista(client, due=_dia(7))
    assert lista["id"].startswith("TDL-")
    assert lista["path"].startswith("todolists/")
    assert (client.ws.root / lista["path"]).exists()
    assert lista["due"] == _dia(7)
    assert lista["progress"] == {"total": 0, "done": 0, "open": 0}


def test_linhas_e_progresso(client):
    lista = _lista(client)
    _linha(client, lista["id"], "Revisar o checklist")
    depois = _linha(client, lista["id"], "Rodar a regressão")
    assert [i["text"] for i in depois["items"]] == [
        "Revisar o checklist", "Rodar a regressão"]
    assert depois["progress"] == {"total": 2, "done": 0, "open": 2}

    marcada = client.put(
        f"/api/v1/todolists/{lista['id']}/items/{depois['items'][0]['id']}",
        json={"done": True}).json()
    assert marcada["progress"] == {"total": 2, "done": 1, "open": 1}


def test_id_de_linha_nunca_e_reaproveitado(client):
    """Reaproveitar o id de uma linha apagada faria um afazer vinculado
    apontar, de repente, para uma linha que não é a dele."""
    lista = _lista(client)
    primeira = _linha(client, lista["id"], "Some depois")["items"][0]["id"]
    client.delete(f"/api/v1/todolists/{lista['id']}/items/{primeira}")

    nova = _linha(client, lista["id"], "Entra no lugar")["items"][0]["id"]
    assert nova != primeira


def test_lista_apagada_vai_para_a_lixeira(client):
    lista = _lista(client)
    assert client.delete(f"/api/v1/todolists/{lista['id']}").status_code == 204
    assert lista["id"] in [i["name"].split("-")[0] + "-" + i["name"].split("-")[1]
                           for i in client.get("/api/v1/trash").json()]


# -- o vínculo, que é um-para-um e mora num lado só --------------------------


def test_linha_vinculada_mostra_o_afazer_resolvido(client):
    """A linha mostra prazo e status do afazer sem quem lê abrir outra tela."""
    afazer = _afazer(client, "Fechar o relatório", due=_dia(2))
    lista = _lista(client)
    resultado = _linha(client, lista["id"], "Relatório final", todo=afazer)

    ref = resultado["items"][0]["todo_ref"]
    assert ref["id"] == afazer
    assert ref["due"] == _dia(2)
    assert ref["status"] == "open"


def test_o_afazer_sabe_de_que_linha_participa(client):
    """Sem guardar o vínculo duas vezes: é consulta, não segundo dado."""
    afazer = _afazer(client, "Ligado a uma linha")
    lista = _lista(client, "Roteiro")
    _linha(client, lista["id"], "O passo dele", todo=afazer)

    visto = client.get(f"/api/v1/todos/{afazer}").json()
    assert visto["list_item"]["list_id"] == lista["id"]
    assert visto["list_item"]["text"] == "O passo dele"
    assert visto["list_item"]["list_title"] == "Roteiro"


def test_um_afazer_participa_de_uma_linha_so(client):
    """Duas linhas apontando para o mesmo afazer tornam "ele está concluído?"
    uma pergunta sem resposta."""
    afazer = _afazer(client)
    primeira = _lista(client, "Lista A")
    _linha(client, primeira["id"], "Passo A", todo=afazer)

    segunda = _lista(client, "Lista B")
    r = client.post(f"/api/v1/todolists/{segunda['id']}/items",
                    json={"text": "Passo B", "todo": afazer})
    assert r.status_code == 409
    erro = r.json()["error"]
    assert erro["code"] == "todo_already_linked"
    assert primeira["id"] in erro["message"]


def test_religar_a_mesma_linha_nao_e_conflito(client):
    afazer = _afazer(client)
    lista = _lista(client)
    criada = _linha(client, lista["id"], "Passo", todo=afazer)
    item_id = criada["items"][0]["id"]

    ok = client.put(f"/api/v1/todolists/{lista['id']}/items/{item_id}",
                    json={"todo": afazer, "text": "Passo revisado"})
    assert ok.status_code == 200


def test_vincular_afazer_inexistente_e_recusado(client):
    lista = _lista(client)
    r = client.post(f"/api/v1/todolists/{lista['id']}/items",
                    json={"text": "x", "todo": "TD-9999"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "todo_not_found"


def test_o_vinculo_sobrevive_ao_reindex(client):
    """Ele mora no arquivo da lista, não no índice — que é descartável."""
    from arbites.indexer import reindex_full

    afazer = _afazer(client)
    lista = _lista(client)
    _linha(client, lista["id"], "Passo", todo=afazer)

    conn = client.app.state.conn
    conn.execute("DELETE FROM todolist_items")
    conn.commit()
    reindex_full(client.ws, conn)

    assert client.get(f"/api/v1/todos/{afazer}").json()["list_item"] is not None


# -- o prazo da lista no sino -----------------------------------------------


def _prazos(client):
    return [i for i in client.get("/api/v1/notifications").json()["items"]
            if i["kind"] == "prazo"]


def test_lista_que_vence_hoje_avisa_com_quantas_linhas_faltam(client):
    lista = _lista(client, "Release de hoje", due=_dia(0))
    _linha(client, lista["id"], "Passo 1")
    _linha(client, lista["id"], "Passo 2")

    aviso = next(p for p in _prazos(client) if p["subject"] == lista["id"])
    assert "vence HOJE" in aviso["message"]
    assert "2 linhas abertas" in aviso["message"]
    assert aviso["target"]["atab"] == "listas"


def test_lista_sem_linha_aberta_nao_cobra_prazo(client):
    """O prazo dela já foi cumprido, ainda que ninguém tenha marcado a lista
    inteira como concluída."""
    lista = _lista(client, "Já terminada", due=_dia(-1))
    criada = _linha(client, lista["id"], "Único passo")
    client.put(f"/api/v1/todolists/{lista['id']}/items/{criada['items'][0]['id']}",
               json={"done": True})

    assert [p for p in _prazos(client) if p["subject"] == lista["id"]] == []


def test_lista_arquivada_nao_cobra_prazo(client):
    lista = _lista(client, "Arquivada", due=_dia(-5))
    _linha(client, lista["id"], "Sobrou aberta")
    client.put(f"/api/v1/todolists/{lista['id']}", json={"status": "archived"})

    assert [p for p in _prazos(client) if p["subject"] == lista["id"]] == []
