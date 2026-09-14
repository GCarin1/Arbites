"""Envio em lote sobre a porta (change 0150, ADR 0015).

## A divisão de trabalho que esta change assume

O agente é a ponte certa para o fluxo com humano no meio: um card, uma story,
um caso — ambiguidade real, decisão humana. Ele é a ponte **errada** para
volume. "Empurrar os 47 resultados do ciclo que fechou" não deveria custar 47
turnos de agente, não deveria custar 47 confirmações, e sobretudo não deveria
variar de uma execução para outra.

Isso é trabalho determinístico: pega o conjunto, compara com o vínculo, age no
delta, registra.

## O que ele entrega HOJE, dito sem enfeite

A orquestração — conjunto → delta → envio → marca → retomada — é real e está
testada. O **transporte**, não: nenhum adaptador de API acompanha esta change.
O adaptador que existe é o de arquivo (change 0148), e é sobre ele e sobre
adaptadores que alguém escreva que este lote roda. Um sistema com capacidade
declarada mas sem transporte é recusado em voz alta, não tentado e falhado.

## As quatro mecânicas que fazem o lote ser confiável

**1. Idempotência pelo vínculo, nunca pela memória de quem chamou.** Repetir o
mesmo lote não duplica porque o que já foi tem vínculo, e o que tem vínculo
sai do delta.

**2. Marca no momento em que vai, item a item.** Não ao fim do lote: falha no
meio com a marca só no fim deixaria metade sincronizada sem registro — e a
retomada reenviaria tudo, duplicando lá.

**3. Conflito sai do lote, não trava o lote.** Um artefato que mudou dos dois
lados precisa de uma pessoa; os outros 46 não têm por que esperar por ele.

**4. Limite de taxa faz recuar, não descartar.** O item volta para a fila e a
tentativa seguinte o pega — perder item de lote é pior do que demorar.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from . import integrations as integ_ops

MAX_TENTATIVAS = 4


class LimiteDeTaxa(Exception):
    """O destino pediu para esperar. Não é falha do item: é ritmo."""

    def __init__(self, segundos: float = 1.0) -> None:
        super().__init__(f"limite de taxa; sugerido esperar {segundos}s")
        self.segundos = segundos


class LoteErro(Exception):
    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class Lote:
    """Um envio de ciclo. Recebe o tracker pronto — quem escolhe o adaptador
    é quem chama, e assim o lote não conhece ferramenta nenhuma."""

    def __init__(self, ws, conn, tracker, system: str,
                 carregar_doc, escrever_doc, reindex) -> None:
        self.ws = ws
        self.conn = conn
        self.tracker = tracker
        self.system = system
        self.carregar_doc = carregar_doc
        self.escrever_doc = escrever_doc
        self.reindex = reindex

    # -- delta -------------------------------------------------------------

    def delta(self, execution: dict[str, Any]) -> dict[str, Any]:
        """O que falta empurrar, o que já está, e o que sai do lote.

        Calculado do disco a cada chamada: a prévia que envelheceu entre a
        tela e o clique é a origem do envio duplicado.
        """
        enviar, ja_estao, em_conflito, sem_caso = [], [], [], []
        for resultado in execution.get("results") or []:
            ct_id = resultado.get("testcase_id")
            linha = self.conn.execute(
                "SELECT id, title, path FROM testcases WHERE id = ?", (ct_id,)
            ).fetchone()
            if not linha:
                sem_caso.append({"testcase_id": ct_id,
                                 "reason": "o caso não está mais no workspace"})
                continue
            try:
                meta, corpo = self.carregar_doc(self.ws, linha["path"])
            except (OSError, ValueError):
                sem_caso.append({"testcase_id": ct_id,
                                 "reason": "arquivo do caso ilegível"})
                continue
            vinculo = integ_ops.link_for(meta, self.system)
            estado = integ_ops.sync_state(
                vinculo, integ_ops.content_hash(corpo),
                resultado.get("remote_revision"),
            )
            item = {
                "testcase_id": ct_id, "title": linha["title"],
                "path": linha["path"], "state": estado,
                "remote_id": (vinculo or {}).get("id"),
                "status": resultado.get("status"),
            }
            if estado == "conflict":
                # sai do lote, e o lote segue: os outros 46 não têm por que
                # esperar por uma decisão que é de pessoa
                item["reason"] = (
                    f"{ct_id} mudou dos dois lados desde a última sincronia —"
                    " precisa de uma pessoa decidindo, e decidir aqui apagaria"
                    " um dos lados em silêncio"
                )
                em_conflito.append(item)
            elif estado == "in_sync":
                ja_estao.append(item)
            else:
                enviar.append(item)

        capacidades = integ_ops.ADAPTADORES.get(self.system)
        return {
            "system": self.system,
            "execution_id": execution.get("id"),
            "to_send": enviar,
            "already_synced": ja_estao,
            "conflicts": em_conflito,
            "unavailable": sem_caso,
            "not_represented": (
                capacidades.nao_representa(["result", "evidence"])
                if capacidades else []
            ),
        }

    # -- envio -------------------------------------------------------------

    async def empurrar(self, execution: dict[str, Any]) -> dict[str, Any]:
        plano = self.delta(execution)
        enviados, falhas = [], []
        parou_por = None

        for item in plano["to_send"]:
            try:
                remoto = await self._enviar_com_recuo(execution, item)
            except LimiteDeTaxa as e:
                # Depois de recuar o quanto podia, PARA — e tudo o que já foi
                # está marcado, então a próxima chamada retoma daqui sem
                # reenviar nada.
                parou_por = "rate_limited"
                falhas.append({"testcase_id": item["testcase_id"],
                               "reason": str(e)})
                break
            except Exception as e:  # noqa: BLE001 — falha do adaptador
                falhas.append({"testcase_id": item["testcase_id"],
                               "reason": str(e)[:200]})
                continue
            self._marcar(item, remoto)
            enviados.append({"testcase_id": item["testcase_id"],
                             "remote_id": remoto.get("remote_id")})

        return {
            "system": self.system,
            "execution_id": execution.get("id"),
            "sent": enviados,
            "failed": falhas,
            "skipped_conflicts": plano["conflicts"],
            "already_synced": [i["testcase_id"] for i in plano["already_synced"]],
            "stopped": parou_por,
        }

    async def _enviar_com_recuo(self, execution: dict, item: dict) -> dict:
        espera = 0.0
        for tentativa in range(MAX_TENTATIVAS):
            try:
                return await self.tracker.upsert(
                    self._artefato(execution, item), item.get("remote_id"))
            except LimiteDeTaxa as e:
                if tentativa == MAX_TENTATIVAS - 1:
                    raise
                espera = e.segundos * (2 ** tentativa)
                await asyncio.sleep(min(espera, 8))
        raise LimiteDeTaxa(espera)  # pragma: no cover — o laço sempre sai antes

    def _artefato(self, execution: dict, item: dict) -> dict[str, Any]:
        resultado = next(
            (r for r in execution.get("results") or []
             if r.get("testcase_id") == item["testcase_id"]), {})
        meta, corpo = self.carregar_doc(self.ws, item["path"])
        return {
            "kind": "result",
            "testcase_id": item["testcase_id"],
            "title": item["title"],
            "body": corpo,
            "execution_id": execution.get("id"),
            "status": resultado.get("status"),
            "executed_at": resultado.get("executed_at"),
            "executed_by": resultado.get("executed_by"),
            "comment": resultado.get("comment"),
            # caminho, não binário: é a capacidade declarada do adaptador de
            # arquivo, e embutir o print aqui quebraria a promessa
            "evidence_paths": [e.get("path") for e in resultado.get("evidences") or []],
            "meta": meta,
        }

    def _marcar(self, item: dict, remoto: dict[str, Any]) -> None:
        """Grava o vínculo NO MOMENTO em que o item foi.

        Marcar só no fim do lote deixaria, numa queda no meio, metade
        sincronizada sem registro — e a retomada reenviaria tudo, duplicando
        no destino exatamente o que já tinha chegado.
        """
        meta, corpo = self.carregar_doc(self.ws, item["path"])
        meta[integ_ops.CAMPO] = integ_ops.upsert_link(
            meta, self.system, str(remoto.get("remote_id")),
            remoto.get("revision"), integ_ops.content_hash(corpo), _agora(),
        )
        caminho = self.ws.root / item["path"]
        self.escrever_doc(caminho, meta, corpo)
        self.reindex(self.ws, self.conn, caminho)


# -- adaptadores com transporte ----------------------------------------------


class FileTracker:
    """O único transporte que acompanha esta change: acumula linhas.

    Não é um mock disfarçado de produto — é o adaptador de arquivo da change
    0148 no formato que a porta pede. O "destino" dele é o CSV que sai no fim,
    e é o que permite empurrar um ciclo para uma ferramenta que só aceita
    planilha.
    """

    capabilities = integ_ops.ADAPTADORES["file"]

    def __init__(self) -> None:
        self.linhas: list[dict[str, Any]] = []

    async def fetch(self, remote_id: str) -> dict[str, Any] | None:
        return next((x for x in self.linhas if x.get("remote_id") == remote_id), None)

    async def upsert(self, artefato: dict[str, Any],
                     remote_id: str | None) -> dict[str, Any]:
        chave = remote_id or f"{artefato['execution_id']}:{artefato['testcase_id']}"
        linha = {"remote_id": chave, "revision": _agora(), **artefato}
        linha.pop("meta", None)
        self.linhas = [x for x in self.linhas if x.get("remote_id") != chave]
        self.linhas.append(linha)
        return {"remote_id": chave, "revision": linha["revision"]}


TRANSPORTES = {"file": FileTracker}


def tracker_para(system: str):
    """Recusa em voz alta o sistema que tem capacidade declarada mas nenhum
    transporte — tentar e falhar diria a mesma coisa mais tarde e pior."""
    if system not in integ_ops.ADAPTADORES:
        raise LoteErro("unknown_system", f"sistema '{system}' não é conhecido")
    if system not in TRANSPORTES:
        raise LoteErro(
            "no_transport",
            f"'{system}' tem capacidades declaradas, mas nenhum transporte"
            " acompanha esta versão: só o adaptador de arquivo empurra lote."
            " Use `file`, ou escreva um adaptador sobre a mesma porta.",
            501,
        )
    return TRANSPORTES[system]()
