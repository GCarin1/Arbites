"""Escritas do agente, com preview obrigatório (change 0147, ADR 0015).

## O que estas três operações resolvem

Ler já funcionava (change 0146). O que faltava era o agente poder **agir** —
e agir sem duplicar, que é onde integrações costumam morrer.

`link_external` parece a menor das três e é a mais importante. Sem ela o
agente não tem como saber que já criou aquele card: numa conversa nova, sem
memória, ele recria — e a duplicata aparece na primeira semana. Com ela o
fluxo vira *"o que daqui ainda não está lá?"* → resposta determinística →
age só no delta. É o que transforma o agente de "cria coisas" em
"sincroniza".

## As três garantias

**1. Preview antes de aplicar.** Toda escrita tem duas rotas: uma que só
CALCULA o que mudaria e uma que grava. Rotas separadas de propósito — o log
de atividade registra o caminho, e um `apply=true` no corpo não apareceria
lá: o registro não conseguiria distinguir "o agente olhou" de "o agente
gravou", que é exatamente a distinção que alguém vai querer depois.

**2. Idempotência pelo vínculo, não pela memória de quem chamou.** A chave
é `(sistema, id remoto)`: se já existe artefato com aquele vínculo, ATUALIZA.
Memória de agente não sobrevive à troca de conversa; vínculo no frontmatter
sobrevive até a um reindex (ADR 0001).

**3. Conflito nunca é resolvido sozinho.** Artefato que mudou dos dois lados
recusa a escrita nomeando o conflito. Último-que-escreve-vence é perda
silenciosa de dado, e numa ferramenta de rastreabilidade é o pior defeito
possível (ADR 0015).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from . import integrations as integ_ops

# Só caso e requisito têm vínculo externo — story nasce no sistema oficial.
VINCULAVEIS = {"testcase": "testcases", "requirement": "requirements"}


class WriteRecusada(Exception):
    """Recusa é RESPOSTA, não acidente: o agente precisa ler o motivo e
    parar, não tentar de novo."""

    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def achar_por_vinculo(
    ws, conn, tabela: str, system: str, remote_id: str,
) -> tuple[str, str, dict[str, Any], str] | None:
    """(entity_id, relpath, meta, corpo) do artefato ligado a `remote_id`.

    Varre o disco em vez do índice: o vínculo mora no frontmatter, e o índice
    é descartável. Com alguns milhares de casos isso é rápido o bastante, e
    ser certo importa mais aqui do que ser rápido — um falso "não existe"
    duplica no sistema oficial.
    """
    import frontmatter

    for row in conn.execute(f"SELECT id, path FROM {tabela} ORDER BY id"):
        caminho = ws.root / row["path"]
        if not caminho.exists():
            continue
        try:
            doc = frontmatter.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        vinculo = integ_ops.link_for(dict(doc.metadata), system)
        if vinculo and str(vinculo.get("id")) == str(remote_id):
            return row["id"], row["path"], dict(doc.metadata), doc.content
    return None


def _recusa_se_em_conflito(meta: dict[str, Any], corpo: str, system: str,
                           revisao_remota: str | None = None) -> None:
    """Recusa se os DOIS lados mudaram desde a última sincronia.

    A revisão remota vem de quem chamou, e é o único jeito honesto: o Arbites
    não fala com o sistema externo (ADR 0015) — quem acabou de olhar o card é
    o agente. Sem ela a pergunta respondida é só "mudou aqui?", e o conflito
    não é detectável. Por isso a detecção é tão forte quanto o `revision` que
    o chamador informa — e não mais do que isso.
    """
    vinculo = integ_ops.link_for(meta, system)
    if not vinculo:
        return
    estado = integ_ops.sync_state(
        vinculo, integ_ops.content_hash(corpo), revisao_remota)
    if estado == "conflict":
        raise WriteRecusada(
            "sync_conflict",
            f"{meta.get('id')} mudou dos DOIS lados desde a última sincronia"
            f" com {system} — escolher um lado aqui apagaria o outro em"
            " silêncio. Resolva o conflito primeiro, com uma pessoa decidindo.",
            409,
        )


# -- caso de teste -----------------------------------------------------------


def previa_testcase(ws, conn, pedido: dict[str, Any]) -> dict[str, Any]:
    """O que a gravação faria. Nada é escrito aqui."""
    system = (pedido.get("system") or "").strip()
    remote_id = str(pedido.get("remote_id") or "").strip()
    if bool(system) != bool(remote_id):
        raise WriteRecusada(
            "incomplete_link",
            "informe `system` e `remote_id` juntos, ou nenhum dos dois: meio"
            " vínculo não torna a chamada idempotente e é assim que a"
            " duplicata nasce.",
        )
    if not (pedido.get("title") or "").strip():
        raise WriteRecusada("missing_title", "o caso precisa de um título")

    existente = (
        achar_por_vinculo(ws, conn, "testcases", system, remote_id)
        if system else None
    )
    if existente:
        entity_id, rel, meta, corpo = existente
        _recusa_se_em_conflito(meta, corpo, system, pedido.get("revision"))
        mudancas = _diferencas(meta, corpo, pedido)
        return {
            "action": "update",
            "entity_id": entity_id,
            "path": rel,
            "reason": f"já existe vínculo {system}:{remote_id} em {entity_id} —"
                      " atualizar em vez de criar é o que impede a duplicata",
            "changes": mudancas,
            "no_op": not mudancas,
        }
    return {
        "action": "create",
        "entity_id": None,
        "path": None,
        "reason": (
            f"nenhum artefato daqui tem vínculo {system}:{remote_id}"
            if system else "sem vínculo informado: nasce sem identidade externa"
        ),
        "changes": [
            {"field": campo, "from": None, "to": pedido.get(campo)}
            for campo in ("title", "type", "priority", "status", "story", "body")
            if pedido.get(campo) is not None
        ],
        "no_op": False,
    }


def _diferencas(meta: dict[str, Any], corpo: str,
                pedido: dict[str, Any]) -> list[dict[str, Any]]:
    mudancas = []
    for campo in ("title", "type", "priority", "status", "story", "squad"):
        novo = pedido.get(campo)
        if novo is None:
            continue
        atual = meta.get(campo)
        if str(atual or "") != str(novo):
            mudancas.append({"field": campo, "from": atual, "to": novo})
    novas_tags = pedido.get("tags")
    if novas_tags is not None and sorted(meta.get("tags") or []) != sorted(novas_tags):
        mudancas.append({"field": "tags", "from": meta.get("tags"), "to": novas_tags})
    novo_corpo = pedido.get("body")
    if novo_corpo is not None and novo_corpo.strip() != (corpo or "").strip():
        mudancas.append({
            "field": "body",
            "from": f"{len(corpo or '')} caracteres",
            "to": f"{len(novo_corpo)} caracteres",
        })
    return mudancas


def _hoje() -> str:
    return date.today().isoformat()


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def aplicar_testcase(ws, conn, pedido: dict[str, Any], autor: str,
                     escrever_doc, reindex) -> dict[str, Any]:
    """Grava. Recalcula a prévia aqui em vez de confiar na que o cliente viu:
    entre o preview e a confirmação alguém pode ter mexido no artefato."""
    plano = previa_testcase(ws, conn, pedido)
    system = (pedido.get("system") or "").strip()
    remote_id = str(pedido.get("remote_id") or "").strip()

    if plano["action"] == "update":
        entity_id, rel, meta, corpo = achar_por_vinculo(
            ws, conn, "testcases", system, remote_id)
        for campo in ("title", "type", "priority", "status", "story", "squad", "tags"):
            if pedido.get(campo) is not None:
                meta[campo] = pedido[campo]
        novo_corpo = pedido.get("body") if pedido.get("body") is not None else corpo
        meta["updated"] = _hoje()
        meta[integ_ops.CAMPO] = integ_ops.upsert_link(
            meta, system, remote_id, pedido.get("revision"),
            integ_ops.content_hash(novo_corpo), _agora(),
        )
        caminho = ws.root / rel
        escrever_doc(caminho, meta, novo_corpo)
        reindex(ws, conn, caminho)
        return {"applied": True, "action": "update", "entity_id": entity_id,
                "path": rel, "plan": plano}

    from .workspace import slugify

    novo_id = ws.next_id("testcase")
    corpo = pedido.get("body") or ""
    meta: dict[str, Any] = {
        "id": novo_id,
        "title": pedido["title"],
        "type": pedido.get("type") or "manual",
        "priority": pedido.get("priority") or "medium",
        "status": pedido.get("status") or "draft",
        "tags": pedido.get("tags") or [],
        "story": pedido.get("story"),
        "created": _hoje(),
        "updated": _hoje(),
        "created_by": autor,
    }
    if pedido.get("squad"):
        meta["squad"] = pedido["squad"]
    if system:
        meta[integ_ops.CAMPO] = integ_ops.upsert_link(
            meta, system, remote_id, pedido.get("revision"),
            integ_ops.content_hash(corpo), _agora(),
        )
    pasta = (pedido.get("folder") or "").strip("/").replace("\\", "/")
    destino = ws.root / "testcases" / pasta if pasta else ws.root / "testcases"
    if not str(destino.resolve()).startswith(str((ws.root / "testcases").resolve())):
        raise WriteRecusada("invalid_folder", "folder fora de testcases/")
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"{novo_id}-{slugify(pedido['title'])}.md"
    escrever_doc(caminho, meta, corpo)
    reindex(ws, conn, caminho)
    return {"applied": True, "action": "create", "entity_id": novo_id,
            "path": ws.relpath(caminho), "plan": plano}


# -- resultado ---------------------------------------------------------------


def previa_resultado(ws, conn, pedido: dict[str, Any], carregar) -> dict[str, Any]:
    exec_id = (pedido.get("execution_id") or "").strip()
    ct_id = (pedido.get("testcase_id") or "").strip()
    status = (pedido.get("status") or "").strip()
    if not exec_id or not ct_id or not status:
        raise WriteRecusada(
            "missing_field",
            "resultado exige `execution_id`, `testcase_id` e `status`")
    execution = carregar(ws, exec_id)
    if execution.get("status") == "closed":
        raise WriteRecusada(
            "execution_closed",
            f"{exec_id} está fechada — resultado em ciclo fechado reescreveria"
            " um retrato que já foi usado para decidir.", 409)
    atual = next((r for r in execution.get("results") or []
                  if r.get("testcase_id") == ct_id), None)
    if atual is None:
        raise WriteRecusada(
            "not_in_execution",
            f"{ct_id} não faz parte de {exec_id} — registrar resultado de um"
            " caso que ninguém planejou executar inventaria cobertura.", 404)
    return {
        "action": "record_result",
        "execution_id": exec_id,
        "testcase_id": ct_id,
        "changes": [{"field": "status", "from": atual.get("status"), "to": status}],
        "evidence": pedido.get("evidence") or [],
        "no_op": atual.get("status") == status and not pedido.get("evidence"),
    }


# Evidência chega em base64, e NÃO como caminho no disco. Um caminho vindo do
# agente seria uma primitiva de leitura de arquivo arbitrário: apontar para
# `/etc/passwd`, deixar o servidor copiar para o workspace e baixar de volta
# pela rota de evidência. base64 não alcança nada que o chamador já não tenha.
LIMITE_EVIDENCIA = 20 * 1024 * 1024


def _decodificar_evidencias(bruto: list[dict[str, Any]]) -> list[tuple]:
    import base64
    import binascii

    saida = []
    for item in bruto or []:
        nome = (item.get("filename") or "").strip()
        if not nome:
            raise WriteRecusada("missing_filename", "evidência exige `filename`")
        try:
            conteudo = base64.b64decode(item.get("content_base64") or "", validate=True)
        except (binascii.Error, ValueError) as e:
            raise WriteRecusada(
                "invalid_evidence",
                f"`content_base64` de {nome} não é base64 válido: {e}") from e
        if not conteudo:
            raise WriteRecusada("empty_evidence", f"{nome} chegou vazio")
        if len(conteudo) > LIMITE_EVIDENCIA:
            raise WriteRecusada(
                "evidence_too_large",
                f"{nome} tem {len(conteudo) // (1024 * 1024)} MB; o limite é"
                f" {LIMITE_EVIDENCIA // (1024 * 1024)} MB")
        saida.append((nome, conteudo, item.get("mime"), item.get("note")))
    return saida


def aplicar_resultado(ws, conn, pedido: dict[str, Any], autor: str,
                      exec_ops, reindex) -> dict[str, Any]:
    plano = previa_resultado(ws, conn, pedido, exec_ops.load)
    evidencias = _decodificar_evidencias(pedido.get("evidence") or [])
    execution = exec_ops.load(ws, pedido["execution_id"])

    exec_ops.set_result_status(
        execution, pedido["testcase_id"], pedido["status"], autor,
        comment=pedido.get("comment"),
    )
    for indice, situacao in (pedido.get("steps") or {}).items():
        exec_ops.set_step_status(
            execution, pedido["testcase_id"], int(indice), situacao, autor)
    gravadas = []
    for nome, conteudo, mime, nota in evidencias:
        gravadas.append(exec_ops.add_evidence(
            ws, execution, pedido["testcase_id"], nome, conteudo, mime, nota, autor,
        )["path"])
    caminho = exec_ops.save(ws, execution)
    reindex(ws, conn, caminho)
    return {"applied": True, "action": "record_result", "plan": plano,
            "evidence_paths": gravadas}


# -- vínculo externo ---------------------------------------------------------


def previa_vinculo(ws, conn, pedido: dict[str, Any], achar_path,
                   carregar_doc) -> dict[str, Any]:
    kind = (pedido.get("kind") or "testcase").strip()
    if kind not in VINCULAVEIS:
        raise WriteRecusada(
            "unlinkable_kind",
            f"só caso de teste e requisito têm vínculo externo; recebido: {kind}")
    entity_id = (pedido.get("entity_id") or "").strip()
    system = (pedido.get("system") or "").strip()
    remote_id = str(pedido.get("remote_id") or "").strip()
    if not entity_id or not system or not remote_id:
        raise WriteRecusada(
            "missing_field", "vínculo exige `entity_id`, `system` e `remote_id`")

    rel = achar_path(conn, VINCULAVEIS[kind], entity_id)
    meta, corpo = carregar_doc(ws, rel)
    _recusa_se_em_conflito(meta, corpo, system, pedido.get("revision"))
    atual = integ_ops.link_for(meta, system)

    # Um id remoto já usado por OUTRO artefato: aceitar criaria dois artefatos
    # daqui apontando para o mesmo card lá, e a próxima sincronia teria de
    # escolher um — sem ter como.
    ja_ligado = achar_por_vinculo(ws, conn, VINCULAVEIS[kind], system, remote_id)
    if ja_ligado and ja_ligado[0] != entity_id:
        raise WriteRecusada(
            "remote_id_taken",
            f"{system}:{remote_id} já está ligado a {ja_ligado[0]} — dois"
            " artefatos daqui apontando para o mesmo item lá tornam a"
            " próxima sincronia indecidível.", 409)

    return {
        "action": "relink" if atual else "link",
        "kind": kind, "entity_id": entity_id, "path": rel,
        "changes": [{"field": f"external.{system}",
                     "from": (atual or {}).get("id"), "to": remote_id}],
        "no_op": bool(atual) and str(atual.get("id")) == remote_id,
    }


def aplicar_vinculo(ws, conn, pedido: dict[str, Any], achar_path, carregar_doc,
                    escrever_doc, reindex) -> dict[str, Any]:
    plano = previa_vinculo(ws, conn, pedido, achar_path, carregar_doc)
    rel = plano["path"]
    meta, corpo = carregar_doc(ws, rel)
    meta[integ_ops.CAMPO] = integ_ops.upsert_link(
        meta, pedido["system"], str(pedido["remote_id"]), pedido.get("revision"),
        integ_ops.content_hash(corpo), _agora(),
    )
    caminho = ws.root / rel
    escrever_doc(caminho, meta, corpo)
    reindex(ws, conn, caminho)
    return {"applied": True, "action": plano["action"],
            "entity_id": plano["entity_id"], "external": meta[integ_ops.CAMPO],
            "plan": plano}
