"""Envio em lote (change 0150, ADR 0015).

Quatro mecânicas, e cada uma existe por causa de um jeito específico de
perder dado: repetir duplica, queda no meio reenvia, um conflito trava 46
itens sãos, e limite de taxa descarta item. Os testes abaixo são um por
buraco.
"""

import asyncio

import pytest
from conftest import login_admin

from arbites import executions as exec_ops
from arbites import integrations as integ_ops
from arbites.api import _load_doc, _write_doc
from arbites.indexer import reindex_file
from arbites.integrations_bulk import FileTracker, LimiteDeTaxa, Lote, tracker_para

CORPO = "## Passos\n\n1. abrir\n\n## Resultado esperado\n\nabre\n"


class TrackerInstavel(FileTracker):
    """Destino que responde limite de taxa, ou cai, sob controle do teste."""

    def __init__(self, limitar_em=(), quebrar_em=(), limites_por_item=1):
        super().__init__()
        self.limitar_em = set(limitar_em)
        self.quebrar_em = set(quebrar_em)
        self.limites_por_item = limites_por_item
        self.vistos: dict[str, int] = {}
        self.chamadas = 0

    async def upsert(self, artefato, remote_id):
        ct = artefato["testcase_id"]
        self.chamadas += 1
        if ct in self.quebrar_em:
            raise RuntimeError(f"destino recusou {ct}")
        if ct in self.limitar_em:
            self.vistos[ct] = self.vistos.get(ct, 0) + 1
            if self.vistos[ct] <= self.limites_por_item:
                raise LimiteDeTaxa(0.01)
        return await super().upsert(artefato, remote_id)


def _montar(client, quantos=3):
    ids = [
        client.post("/api/v1/testcases",
                    json={"title": f"Caso {i}", "body": CORPO}).json()["id"]
        for i in range(quantos)
    ]
    execucao = client.post("/api/v1/executions", json={
        "name": "Ciclo para empurrar", "owner": "qa", "testcase_ids": ids,
    }).json()["id"]
    for ct in ids:
        client.put(f"/api/v1/executions/{execucao}/results/{ct}",
                   json={"status": "passed"})
    return execucao, ids


def _lote(client, tracker, system="file"):
    return Lote(client.ws, client.app.state.conn, tracker, system,
                _load_doc, _write_doc, reindex_file)


def _empurrar(client, tracker, exec_id):
    execution = exec_ops.load(client.ws, exec_id)
    return asyncio.run(_lote(client, tracker).empurrar(execution))


# -- o delta -----------------------------------------------------------------


def test_previa_mostra_o_delta_antes_de_qualquer_escrita(client):
    execucao, ids = _montar(client)
    plano = client.get(f"/api/v1/integrations/bulk/{execucao}/preview").json()

    assert [i["testcase_id"] for i in plano["to_send"]] == ids
    assert plano["already_synced"] == []
    assert plano["conflicts"] == []
    # e nada foi gravado: nenhum caso ganhou vínculo
    for ct in ids:
        meta, _ = _load_doc(client.ws, _caminho(client, ct))
        assert integ_ops.link_for(meta, "file") is None


def _caminho(client, ct_id: str) -> str:
    return client.app.state.conn.execute(
        "SELECT path FROM testcases WHERE id = ?", (ct_id,)).fetchone()["path"]


# -- repetir não duplica -----------------------------------------------------


def test_empurrar_o_mesmo_ciclo_duas_vezes_nao_duplica_no_destino(client):
    """A idempotência vem do vínculo: o que já foi tem vínculo, e o que tem
    vínculo sai do delta."""
    execucao, ids = _montar(client)
    destino = FileTracker()

    primeira = _empurrar(client, destino, execucao)
    assert len(primeira["sent"]) == 3
    assert len(destino.linhas) == 3

    segunda = _empurrar(client, destino, execucao)
    assert segunda["sent"] == []
    assert sorted(segunda["already_synced"]) == sorted(ids)
    assert len(destino.linhas) == 3  # o destino não cresceu


# -- retomada ----------------------------------------------------------------


def test_interromper_no_meio_e_repetir_continua_de_onde_parou(client):
    """A marca vai item a item, no momento em que ele vai. Marcar só no fim
    deixaria, numa queda no meio, metade sincronizada sem registro — e a
    retomada reenviaria tudo, duplicando lá."""
    execucao, ids = _montar(client)
    # o segundo caso derruba o envio; o primeiro já foi
    quebrado = TrackerInstavel(quebrar_em={ids[1]})

    parcial = _empurrar(client, quebrado, execucao)
    assert [s["testcase_id"] for s in parcial["sent"]] == [ids[0], ids[2]]
    assert [f["testcase_id"] for f in parcial["failed"]] == [ids[1]]

    # agora o destino se comporta: só o que faltou é reenviado
    saudavel = TrackerInstavel()
    saudavel.linhas = list(quebrado.linhas)
    retomada = _empurrar(client, saudavel, execucao)
    assert [s["testcase_id"] for s in retomada["sent"]] == [ids[1]]
    assert saudavel.chamadas == 1  # nada do que já tinha ido foi reenviado


# -- conflito ----------------------------------------------------------------


def test_conflito_sai_do_lote_e_o_restante_segue(client):
    """Um artefato que precisa de pessoa não tem por que travar os outros."""
    execucao, ids = _montar(client)
    conflitado = ids[1]

    # última sincronia com um hash que não é mais o do corpo de agora...
    client.put(f"/api/v1/integrations/links/testcase/{conflitado}",
               json={"system": "file", "id": "REMOTO-1", "revision": "v1",
                     "synced_hash": "hash-antigo"})
    # ...e o lado de lá também avançou, o que o resultado informa
    execution = exec_ops.load(client.ws, execucao)
    for r in execution["results"]:
        if r["testcase_id"] == conflitado:
            r["remote_revision"] = "v2"
    exec_ops.save(client.ws, execution)

    destino = FileTracker()
    resultado = asyncio.run(
        _lote(client, destino).empurrar(exec_ops.load(client.ws, execucao)))

    assert [s["testcase_id"] for s in resultado["sent"]] == [ids[0], ids[2]]
    fora = resultado["skipped_conflicts"]
    assert [c["testcase_id"] for c in fora] == [conflitado]
    assert "dois lados" in fora[0]["reason"]
    assert len(destino.linhas) == 2  # o conflitado não foi empurrado


# -- limite de taxa ----------------------------------------------------------


def test_limite_de_taxa_faz_recuar_e_retomar_sem_perder_item(client):
    """Perder item de lote é pior do que demorar."""
    execucao, ids = _montar(client)
    # o do meio responde limite de taxa duas vezes e depois aceita
    destino = TrackerInstavel(limitar_em={ids[1]}, limites_por_item=2)

    resultado = _empurrar(client, destino, execucao)

    assert sorted(s["testcase_id"] for s in resultado["sent"]) == sorted(ids)
    assert resultado["failed"] == []
    # duas recusas e a terceira aceita: recuou e voltou em vez de descartar
    assert destino.vistos[ids[1]] == 3


def test_limite_persistente_para_o_lote_mas_o_que_foi_fica_marcado(client):
    """Depois de recuar o quanto pôde, para — e a próxima chamada retoma
    daqui, porque o que já foi está marcado."""
    execucao, ids = _montar(client)
    teimoso = TrackerInstavel(limitar_em={ids[1]}, limites_por_item=99)

    parcial = _empurrar(client, teimoso, execucao)
    assert parcial["stopped"] == "rate_limited"
    assert [s["testcase_id"] for s in parcial["sent"]] == [ids[0]]
    # o terceiro nem foi tentado: o lote parou no segundo
    assert ids[2] not in [s["testcase_id"] for s in parcial["sent"]]

    saudavel = TrackerInstavel()
    saudavel.linhas = list(teimoso.linhas)
    retomada = _empurrar(client, saudavel, execucao)
    assert sorted(s["testcase_id"] for s in retomada["sent"]) == sorted(ids[1:])


# -- transporte --------------------------------------------------------------


def test_sistema_sem_transporte_e_recusado_em_voz_alta(client):
    """Capacidade declarada não é transporte. Tentar e falhar diria a mesma
    coisa mais tarde e pior."""
    from arbites.integrations_bulk import LoteErro

    with pytest.raises(LoteErro) as e:
        tracker_para("businessmap")
    assert e.value.code == "no_transport"
    assert "nenhum transporte" in e.value.message

    execucao, _ = _montar(client, 1)
    r = client.post(f"/api/v1/integrations/bulk/{execucao}",
                    params={"system": "businessmap"})
    assert r.status_code == 501
    assert r.json()["error"]["code"] == "no_transport"


def test_sistema_desconhecido_e_recusado(client):
    execucao, _ = _montar(client, 1)
    r = client.get(f"/api/v1/integrations/bulk/{execucao}/preview",
                   params={"system": "inventado"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unknown_system"


def test_empurrar_pela_rota_marca_o_vinculo_no_arquivo(client):
    """Marca no frontmatter, não só no índice: reindex não pode apagar a
    memória do que já foi sincronizado (ADR 0001)."""
    execucao, ids = _montar(client, 2)
    resultado = client.post(f"/api/v1/integrations/bulk/{execucao}").json()
    assert len(resultado["sent"]) == 2

    for ct in ids:
        meta, _ = _load_doc(client.ws, _caminho(client, ct))
        assert integ_ops.link_for(meta, "file")["id"]

    repetido = client.post(f"/api/v1/integrations/bulk/{execucao}").json()
    assert repetido["sent"] == []
