"""O sino: notificações DERIVADAS do estado vivo (change 0161).

## Por que derivar em vez de gravar

Uma caixa de entrada gravada cria um SEGUNDO estado, e o segundo estado
diverge do primeiro: o aviso corrigido continua na lista, quem clica descobre
que não há nada lá, e alguém age sobre um buraco que não existe. Esse defeito
exato já apareceu aqui — story sem epic dada como descoberta (change 0158) —
e é o pior tipo, porque parece informação.

Então a notificação é **calculada das fontes que já são verdade**: os avisos do
índice, a credencial, o painel de observabilidade, os registros no disco. Some
quando o motivo some. É o mesmo princípio do resto do produto: o filesystem é
a verdade (ADR 0001) e a marca d'água da ingestão é derivada do disco, não
guardada (ADR 0016).

## O que É gravado, e só isso

Por usuário, no banco durável (ADR 0011): **o que você leu** e **até onde
limpou**. É pequeno, é genuinamente por pessoa, e não tem como divergir de
nada — porque não descreve o mundo, descreve você.

Cada notificação carrega um **id estável** (hash da origem + chave), então
"lido" gruda mesmo quando a lista inteira é recalculada do zero.

## As quatro origens

- `problema` — avisos do índice e da credencial. A aba Problemas vira UMA das
  fontes do sino, e continua existindo: o sino é ambiente, a aba é triagem.
- `observabilidade` — o que mudou sozinho: quebrou, virou instável, o silêncio
  da ingestão, sinal que regrediu.
- `feito` — ação do SISTEMA que deu certo: ingestão trouxe execuções, rodada
  de auditoria concluída, ciclo fechado. São as que acontecem sem ninguém
  olhando — por isso merecem aviso, e por isso "criei um CT agora" não entra.
- `info` — o log de atividade, só para admin e só com o interruptor ligado.
  Nasce desligado: quem quer o ruído liga de propósito.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

# Quanto do passado o sino enxerga. Não é retenção — nada é apagado aqui;
# é só até onde vale a pena olhar para trás num aviso de canto de tela.
JANELA_DIAS = 14
LIMITE = 60


def _id(*partes: Any) -> str:
    """Id ESTÁVEL: o mesmo motivo produz o mesmo id em toda recontagem, senão
    "lido" se perderia a cada recálculo e o sino voltaria a piscar sozinho."""
    bruto = "|".join(str(p) for p in partes)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:16]


def _sem_repetir(subject: str, message: str) -> str:
    """O assunto vai no destaque; repeti-lo no começo da frase o diz duas
    vezes seguidas ("`lcp_ms` lcp_ms piorou 23%"), e a segunda não acrescenta
    nada — só empurra o resto da frase para fora da linha."""
    if subject and message.startswith(subject + " "):
        resto = message[len(subject) + 1:]
        return resto[0].lower() + resto[1:] if resto else message
    return message


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(valor: Any) -> str:
    if not valor:
        return _agora().isoformat()
    return str(valor)


# -- as fontes ---------------------------------------------------------------


def _dos_problemas(avisos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saida = []
    for aviso in avisos:
        origem = aviso.get("source_path") or ""
        saida.append({
            "id": _id("problema", origem, aviso.get("code")),
            "kind": "problema",
            "severity": "problem",
            # O nome do arquivo em destaque, separado da frase: destacar por
            # regex dentro da mensagem erra na primeira mensagem diferente.
            "subject": origem.rsplit("/", 1)[-1] or origem,
            "subject_full": origem,
            "message": aviso.get("message") or "",
            "at": _iso(aviso.get("created_at")),
            "target": _alvo_do_caminho(origem),
        })
    return saida


_ID_NO_NOME = re.compile(r"\b([A-Z]{2,6}-\d{3,})\b")


def _alvo_do_caminho(caminho: str) -> dict[str, Any]:
    """Para onde clicar leva. Caminho do workspace vira a aba daquela área;
    o que não é caminho (a credencial, por exemplo) cai em Problemas.

    Quando o nome do arquivo carrega um ID, o alvo é o ITEM e não a lista:
    cair na lista e ter de procurar de novo é metade de um link.
    """
    topo = (caminho or "").split("/", 1)[0]
    por_area = {
        "testcases": "testcases", "requirements": "requirements",
        "defects": "defects", "todos": "todos", "decisions": "decisions",
        "meetings": "meetings", "audits": "audit", "executions": "executions",
        "ci": "observability",
    }
    aba = por_area.get(topo)
    if not aba:
        return {"tab": "problems"}
    achado = _ID_NO_NOME.search(caminho.rsplit("/", 1)[-1])
    if achado:
        return {"tab": aba, "id": achado.group(1), "path": caminho}
    return {"tab": aba, "path": caminho}


def _da_observabilidade(painel: dict[str, Any]) -> list[dict[str, Any]]:
    """Mudança de observabilidade é sobre um PERÍODO, não um instante.

    O instante que a representa é o da última execução: é ela que fez o
    período ser o que é. Usar "agora" pareceria certo e quebraria duas coisas
    — toda mudança apareceria como recém-chegada, e "limpar" não limparia
    nada, porque na chamada seguinte o "agora" já seria maior que a marca
    d'água e o item voltaria na hora.
    """
    quando = (painel.get("health") or {}).get("last_run_at") \
        or painel.get("period", {}).get("since")
    saida = []
    for mudanca in painel.get("changes") or []:
        chave = (mudanca.get("signal") or mudanca.get("scenario")
                 or mudanca.get("run_id") or "")
        saida.append({
            "id": _id("obs", mudanca.get("kind"), chave, mudanca.get("text")),
            "kind": "observabilidade",
            "severity": "attention",
            "subject": (mudanca.get("testcase_id") or mudanca.get("signal")
                        or mudanca.get("scenario") or mudanca.get("run_id") or ""),
            "subject_full": mudanca.get("run_id") or "",
            "message": _sem_repetir(
                (mudanca.get("testcase_id") or mudanca.get("signal")
                 or mudanca.get("scenario") or ""),
                mudanca.get("text") or "",
            ),
            "at": _iso(quando),
            "target": ({"tab": "observability", "run": mudanca["run_id"]}
                       if mudanca.get("run_id") else {"tab": "observability"}),
        })
    return saida


def _dos_prazos(conn) -> list[dict[str, Any]]:
    """Afazer vencido e afazer que vence hoje.

    Faltava, e era o buraco mais óbvio: o produto tem prazo desde sempre e o
    sino não olhava para ele. Um aviso que chega depois do prazo não é aviso.

    O id inclui o DIA de hoje de propósito: um afazer vencido volta a não-lido
    a cada dia que passa. Silenciar para sempre algo que está vencido é o
    contrário do que um lembrete faz — e quanto mais atrasado, mais ele deve
    incomodar, não menos. O que vence hoje aparece uma vez, porque `hoje` e o
    prazo são o mesmo dia.
    """
    hoje = _agora().date().isoformat()
    saida = []
    for linha in conn.execute(
        "SELECT id, title, due, status, path FROM todos"
        " WHERE due IS NOT NULL AND due <> '' AND COALESCE(status, '') <> 'done'"
        " AND due <= ? ORDER BY due", (hoje,),
    ):
        vencido = linha["due"] < hoje
        if vencido:
            try:
                dias = (date.fromisoformat(hoje)
                        - date.fromisoformat(linha["due"])).days
            except ValueError:
                dias = 0
            texto = (f"venceu ontem" if dias == 1
                     else f"venceu há {dias} dias") + f" ({linha['due']})"
        else:
            texto = "vence HOJE"
        saida.append({
            "id": _id("todo_due", linha["id"], linha["due"], hoje),
            "kind": "prazo",
            # Vencido é problema; vence hoje ainda dá tempo, é atenção.
            "severity": "problem" if vencido else "attention",
            "subject": linha["id"],
            "subject_full": linha["path"] or linha["id"],
            "message": f"{linha['title']} — {texto}",
            # O instante é HOJE, e não o prazo: com o prazo no passado, a
            # marca d'água de "limpar" o esconderia para sempre.
            "at": hoje + "T00:00:00+00:00",
            "target": {"tab": "todos", "id": linha["id"]},
        })

    # A LISTA também tem prazo (change 0164). A linha não tem: quando ela
    # precisa de um, liga-se a um afazer — que já está no laço acima.
    for linha in conn.execute(
        "SELECT id, title, due, path,"
        " (SELECT COUNT(*) FROM todolist_items i"
        "   WHERE i.list_id = todolists.id AND COALESCE(i.done, 0) = 0) AS abertas"
        " FROM todolists WHERE due IS NOT NULL AND due <> ''"
        " AND COALESCE(status, '') = 'active' AND due <= ? ORDER BY due", (hoje,),
    ):
        vencida = linha["due"] < hoje
        abertas = linha["abertas"] or 0
        if abertas == 0:
            # Lista sem linha aberta não cobra prazo: o prazo dela já foi
            # cumprido, ainda que ninguém tenha marcado a lista como concluída.
            continue
        try:
            dias = (date.fromisoformat(hoje) - date.fromisoformat(linha["due"])).days
        except ValueError:
            dias = 0
        quando = ("vence HOJE" if not vencida else
                  "venceu ontem" if dias == 1 else f"venceu há {dias} dias")
        restam = ("1 linha aberta" if abertas == 1 else f"{abertas} linhas abertas")
        saida.append({
            "id": _id("list_due", linha["id"], linha["due"], hoje),
            "kind": "prazo",
            "severity": "problem" if vencida else "attention",
            "subject": linha["id"],
            "subject_full": linha["path"] or linha["id"],
            "message": f"{linha['title']} — {quando}, com {restam}",
            "at": hoje + "T00:00:00+00:00",
            "target": {"tab": "todos", "atab": "listas", "id": linha["id"]},
        })
    return saida


def _do_sistema(conn, desde: str) -> list[dict[str, Any]]:
    """Ação do sistema que deu certo — a que aconteceu sem ninguém olhando."""
    saida: list[dict[str, Any]] = []

    # Ingestão: AGRUPADA por lote (mesmo minuto). Uma linha por run faria a
    # primeira ingestão despejar cinquenta avisos de uma vez, e um sino que
    # grita cinquenta vezes é um sino que ninguém olha mais.
    for linha in conn.execute(
        "SELECT substr(ingested_at, 1, 16) AS lote, COUNT(*) AS n,"
        " MAX(ingested_at) AS at, MAX(repo) AS repo"
        " FROM ci_runs WHERE ingested_at >= ? GROUP BY lote"
        " ORDER BY at DESC LIMIT 20", (desde,),
    ):
        quantas = linha["n"]
        saida.append({
            "id": _id("ingest", linha["lote"]),
            "kind": "feito",
            "severity": "done",
            "subject": linha["repo"] or "CI",
            "subject_full": linha["repo"] or "",
            "message": (
                f"{quantas} execução de CI ingerida" if quantas == 1
                else f"{quantas} execuções de CI ingeridas"
            ) + " — os sinais e os anexos já estão na Observabilidade.",
            "at": _iso(linha["at"]),
            "target": {"tab": "observability"},
        })

    for linha in conn.execute(
        "SELECT id, ran_at, total, path FROM audits WHERE ran_at >= ?"
        " ORDER BY ran_at DESC LIMIT 10", (desde,),
    ):
        total = linha["total"] or 0
        saida.append({
            "id": _id("audit", linha["id"]),
            "kind": "feito",
            "severity": "done",
            "subject": (linha["path"] or "").rsplit("/", 1)[-1] or linha["id"],
            "subject_full": linha["path"] or "",
            "message": (
                "rodada de auditoria concluída sem achados" if total == 0
                else f"rodada de auditoria concluída com {total} "
                     + ("achado" if total == 1 else "achados")
            ),
            "at": _iso(linha["ran_at"]),
            "target": {"tab": "audit", "id": linha["id"]},
        })

    for linha in conn.execute(
        "SELECT id, name, closed_at FROM executions WHERE closed_at >= ?"
        " ORDER BY closed_at DESC LIMIT 10", (desde,),
    ):
        saida.append({
            "id": _id("exec_closed", linha["id"]),
            "kind": "feito",
            "severity": "done",
            "subject": linha["id"],
            "subject_full": linha["id"],
            "message": f"ciclo \"{linha['name']}\" foi fechado",
            "at": _iso(linha["closed_at"]),
            "target": {"tab": "executions", "id": linha["id"]},
        })
    return saida


def _do_log(auth_conn, desde: str, limite: int = 30) -> list[dict[str, Any]]:
    """O log de atividade. Só admin, só com o interruptor ligado — é o único
    volume que pode inundar o sino, e por isso é opcional."""
    saida = []
    for linha in auth_conn.execute(
        "SELECT at, user_email, method, path, status_code FROM activity"
        " WHERE at >= ? AND status_code < 400 ORDER BY at DESC LIMIT ?",
        (desde, limite),
    ):
        caminho = linha["path"] or ""
        saida.append({
            "id": _id("activity", linha["at"], linha["method"], caminho),
            "kind": "info",
            "severity": "info",
            "subject": caminho.rsplit("/", 1)[-1] or caminho,
            "subject_full": caminho,
            "message": f"{linha['user_email']} — {linha['method']} {caminho}"
                       f" ({linha['status_code']})",
            "at": _iso(linha["at"]),
            "target": {"tab": "admin", "atab": "atividade"},
        })
    return saida


# -- a lista ----------------------------------------------------------------


def listar(
    conn, auth_conn, user: dict[str, Any], avisos: list[dict[str, Any]],
    painel: dict[str, Any] | None, com_log: bool,
) -> dict[str, Any]:
    desde_janela = (_agora() - timedelta(days=JANELA_DIAS)).isoformat()
    limpo_ate = _limpo_ate(auth_conn, user["id"])
    desde = max(desde_janela, limpo_ate) if limpo_ate else desde_janela

    itens = _dos_problemas(avisos) + _dos_prazos(conn) + _do_sistema(conn, desde)
    if painel is not None:
        itens += _da_observabilidade(painel)
    if com_log:
        itens += _do_log(auth_conn, desde)

    # O que foi limpo some — inclusive o problema que ainda existe. Limpar é
    # dizer "eu vi"; se o motivo persistir, ele volta no próximo evento dele.
    if limpo_ate:
        itens = [i for i in itens if i["at"] > limpo_ate]

    lidos = _lidos(auth_conn, user["id"])
    for item in itens:
        item["read"] = item["id"] in lidos
    itens.sort(key=lambda i: i["at"], reverse=True)
    itens = itens[:LIMITE]
    return {
        "items": itens,
        "unread": sum(1 for i in itens if not i["read"]),
        "cleared_at": limpo_ate,
    }


# -- o estado por usuário (o único pedaço gravado) ---------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS notification_reads(
  user_id TEXT NOT NULL, notification_id TEXT NOT NULL, read_at TEXT,
  PRIMARY KEY (user_id, notification_id));
CREATE TABLE IF NOT EXISTS notification_clears(
  user_id TEXT PRIMARY KEY, cleared_at TEXT NOT NULL);
"""


def _lidos(auth_conn, user_id: str) -> set[str]:
    return {
        linha["notification_id"] for linha in auth_conn.execute(
            "SELECT notification_id FROM notification_reads WHERE user_id = ?",
            (user_id,))
    }


def _limpo_ate(auth_conn, user_id: str) -> str:
    linha = auth_conn.execute(
        "SELECT cleared_at FROM notification_clears WHERE user_id = ?",
        (user_id,)).fetchone()
    return linha["cleared_at"] if linha else ""


def marcar(auth_conn, user_id: str, notification_id: str, lido: bool) -> None:
    if lido:
        auth_conn.execute(
            "INSERT OR REPLACE INTO notification_reads"
            " (user_id, notification_id, read_at) VALUES (?, ?, ?)",
            (user_id, notification_id, _agora().isoformat()))
    else:
        auth_conn.execute(
            "DELETE FROM notification_reads WHERE user_id = ? AND"
            " notification_id = ?", (user_id, notification_id))
    auth_conn.commit()


def marcar_todas(auth_conn, user_id: str, ids: list[str]) -> int:
    agora = _agora().isoformat()
    auth_conn.executemany(
        "INSERT OR REPLACE INTO notification_reads"
        " (user_id, notification_id, read_at) VALUES (?, ?, ?)",
        [(user_id, i, agora) for i in ids])
    auth_conn.commit()
    return len(ids)


def limpar(auth_conn, user_id: str) -> str:
    """Limpar é uma marca d'água, não um DELETE de notificação.

    Não há o que apagar: a lista é derivada. O que se grava é "vi tudo até
    aqui" — e por isso limpar nunca perde um motivo que continua valendo, ele
    só reaparece quando voltar a acontecer.
    """
    agora = _agora().isoformat()
    auth_conn.execute(
        "INSERT OR REPLACE INTO notification_clears (user_id, cleared_at)"
        " VALUES (?, ?)", (user_id, agora))
    # As marcas de leitura anteriores viram lixo: o que elas descreviam não
    # aparece mais.
    auth_conn.execute(
        "DELETE FROM notification_reads WHERE user_id = ?", (user_id,))
    auth_conn.commit()
    return agora
