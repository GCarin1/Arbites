"""Lixeira (0081) — listar, restaurar e esvaziar itens de .arbites/trash/
pela API. Todo delete move para a lixeira (nunca apaga); o restore devolve
ao caminho de origem e reindexa."""


def test_deleted_ct_appears_in_trash_and_restores(client):
    ct = client.post("/api/v1/testcases", json={"title": "Some depois volta"}).json()
    origin_rel = ct["path"]
    client.delete(f"/api/v1/testcases/{ct['id']}")

    # some do índice, mas aparece na lixeira com a origem registrada
    assert client.get(f"/api/v1/testcases/{ct['id']}").status_code == 404
    trash = client.get("/api/v1/trash").json()
    assert len(trash) == 1
    item = trash[0]
    assert item["origin"] == origin_rel
    assert item["kind"] == "testcases"
    assert item["trashed_at"]

    # restaura → volta ao índice e ao caminho original
    resp = client.post(f"/api/v1/trash/{item['name']}/restore")
    assert resp.status_code == 200
    assert resp.json()["restored"] == origin_rel
    assert client.get(f"/api/v1/testcases/{ct['id']}").status_code == 200
    assert client.get("/api/v1/trash").json() == []


def test_empty_trash_clears_everything(client):
    for i in range(3):
        d = client.post("/api/v1/testcases", json={"title": f"CT {i}"}).json()
        client.delete(f"/api/v1/testcases/{d['id']}")
    assert len(client.get("/api/v1/trash").json()) == 3

    resp = client.delete("/api/v1/trash")
    assert resp.json()["removed"] == 3
    assert client.get("/api/v1/trash").json() == []


def test_restore_unknown_name_is_404(client):
    assert client.post("/api/v1/trash/nada.md/restore").status_code == 404


def test_restore_does_not_overwrite_existing(client):
    ct = client.post("/api/v1/testcases", json={"title": "Colisão"}).json()
    client.delete(f"/api/v1/testcases/{ct['id']}")
    name = client.get("/api/v1/trash").json()[0]["name"]
    # recria um CT no mesmo caminho de origem (mesmo id não, mas mesmo arquivo)
    # força colisão criando um arquivo no destino antes do restore
    (client.ws.root / ct["path"]).write_text("---\nid: X\n---\n", encoding="utf-8")

    restored = client.post(f"/api/v1/trash/{name}/restore").json()["restored"]
    # não sobrescreveu: restaurou com sufixo
    assert restored != ct["path"]
    assert (client.ws.root / ct["path"]).read_text(encoding="utf-8").startswith("---")
