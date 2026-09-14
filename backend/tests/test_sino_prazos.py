"""O sino e os prazos dos afazeres (change 0163).

O defeito: o produto tem prazo desde sempre e o sino não olhava para ele.
Um aviso que chega depois do prazo não é aviso.
"""

from datetime import date, timedelta

import pytest
from conftest import login_admin


def _dia(delta: int) -> str:
    return (date.today() + timedelta(days=delta)).isoformat()


def _prazos(client) -> list[dict]:
    return [i for i in client.get("/api/v1/notifications").json()["items"]
            if i["kind"] == "prazo"]


def test_afazer_que_vence_hoje_aparece_no_sino(client):
    """O caso reportado: prazo para hoje e nenhum aviso."""
    todo = client.post("/api/v1/todos", json={
        "title": "Revisar a regressão", "due": _dia(0)}).json()["id"]

    aviso = next(p for p in _prazos(client) if p["subject"] == todo)
    assert "vence HOJE" in aviso["message"]
    assert "Revisar a regressão" in aviso["message"]
    assert aviso["severity"] == "attention"      # ainda dá tempo
    assert aviso["target"] == {"tab": "todos", "id": todo}


def test_afazer_vencido_aparece_como_problema_com_quantos_dias(client):
    todo = client.post("/api/v1/todos", json={
        "title": "Atrasado", "due": _dia(-3)}).json()["id"]

    aviso = next(p for p in _prazos(client) if p["subject"] == todo)
    assert "venceu há 3 dias" in aviso["message"]
    assert aviso["severity"] == "problem"        # já passou: é problema


def test_vencido_ontem_fala_no_singular(client):
    client.post("/api/v1/todos", json={"title": "De ontem", "due": _dia(-1)})
    assert any("venceu ontem" in p["message"] for p in _prazos(client))


def test_afazer_futuro_nao_enche_o_sino(client):
    """Avisar com antecedência encheria a lista de coisa sobre a qual ninguém
    vai agir hoje — a decisão foi avisar no dia, como o Microsoft To Do."""
    client.post("/api/v1/todos", json={"title": "Semana que vem", "due": _dia(5)})
    assert _prazos(client) == []


def test_afazer_concluido_nao_cobra_prazo(client):
    todo = client.post("/api/v1/todos", json={
        "title": "Já feito", "due": _dia(-2)}).json()["id"]
    assert _prazos(client)

    client.put(f"/api/v1/todos/{todo}", json={"status": "done"})
    assert _prazos(client) == []


def test_afazer_sem_prazo_nao_gera_aviso(client):
    client.post("/api/v1/todos", json={"title": "Sem data"})
    assert _prazos(client) == []


def test_vencido_volta_a_nao_lido_a_cada_dia(client):
    """Silenciar para sempre algo que está vencido é o contrário do que um
    lembrete faz: quanto mais atrasado, mais deve incomodar."""
    from arbites import notifications as notif_ops

    hoje = date.today().isoformat()
    amanha = (date.today() + timedelta(days=1)).isoformat()
    ontem_id = notif_ops._id("todo_due", "TD-0001", _dia(-2), hoje)
    amanha_id = notif_ops._id("todo_due", "TD-0001", _dia(-2), amanha)
    assert ontem_id != amanha_id


def test_o_instante_do_aviso_e_hoje_e_nao_o_prazo_passado(client):
    """Com o prazo no passado, a marca d'água de "limpar" o esconderia para
    sempre — e um vencido não pode sumir por ter sido limpo uma vez."""
    client.post("/api/v1/todos", json={"title": "Antigo", "due": _dia(-30)})
    aviso = _prazos(client)[0]
    assert aviso["at"].startswith(date.today().isoformat())
