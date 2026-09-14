"""Ingestão de execuções de CI que o Arbites NÃO disparou (changes 0153/0154).

Até aqui o Arbites só conhecia run que ele mesmo começou (`CIManager.dispatch`).
Um cron que nasce no GitHub — justamente o que roda toda semana colhendo
telemetria, logs, acessibilidade e prints — era invisível.

## As três decisões que mandam neste arquivo (ADR 0016)

**1. O run vira ARQUIVO no workspace, não linha no índice.**
O índice é descartável (ADR 0001): um reindex o reconstrói do zero. Se a
história da observabilidade morasse só lá, um reindex apagaria meses de série
temporal. Cada run ingerido vira `ci/<ano>/<chave>.md`, com os sinais no
frontmatter e a análise no corpo; os anexos ficam ao lado. O índice só
indexa, como faz com todo o resto.

**2. A marca d'água é DERIVADA do que está no disco.**
Nada de um contador guardado à parte, que sai de sincronia com a realidade na
primeira falha no meio. "O que já ingeri" é uma pergunta que o próprio
conteúdo responde — e daí a idempotência e a retomada caem de graça: ligar o
computador depois de uma semana fora traz a semana inteira, porque a resposta
é "o que ainda não tem arquivo".

**3. Quem produz DECLARA, por manifesto.**
O artifact traz um `arbites.json` dizendo quais sinais tem e onde estão os
anexos. Sem manifesto o Arbites cai num modo de convenção por nome de
arquivo — e ANUNCIA que caiu, porque convenção quebra em silêncio quando
alguém renomeia um arquivo.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter

MANIFESTO = "arbites.json"
VERSAO_MANIFESTO = 1

# Convenção de nome — o FALLBACK, para quando o workflow não pode ser
# alterado. Anunciado como fallback de propósito: ele acerta hoje e quebra
# calado no dia em que alguém renomear o arquivo.
CONVENCAO = {
    "analysis": re.compile(r"(analysis|analise|relatorio)\.md$", re.I),
    "log": re.compile(r"\.(log|txt)$", re.I),
    "screenshot": re.compile(r"\.(png|jpe?g|webp)$", re.I),
    "cucumber": re.compile(r"(result|cucumber)\.json$", re.I),
}


class IngestError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def run_key(provider: str, run_id: int | str) -> str:
    """Chave estável do run. É ela que dá a idempotência: ingerir duas vezes
    escreve o mesmo arquivo, não cria um segundo."""
    return f"{provider}-{run_id}"


def _slug(texto: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", texto).strip("-").lower()


def caminho_do_run(chave: str, quando: str | None) -> str:
    """`ci/<ano>/<chave>.md` — o ano é a pasta natural, como nas execuções."""
    ano = (quando or "")[:4] or datetime.now(timezone.utc).strftime("%Y")
    return f"ci/{ano}/{chave}.md"


# -- manifesto ---------------------------------------------------------------


def ler_manifesto(arquivos: dict[str, bytes]) -> tuple[dict[str, Any], str | None]:
    """Lê o manifesto do artifact. Devolve (manifesto, aviso).

    `aviso` preenchido significa que caímos no modo convenção — e quem chamou
    precisa propagar isso, não engolir: o valor do manifesto está justamente
    em não depender de nome de arquivo.
    """
    for nome, bruto in arquivos.items():
        if Path(nome).name == MANIFESTO:
            try:
                dados = json.loads(bruto.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise IngestError(
                    "manifest_invalid",
                    f"{MANIFESTO} presente mas ilegível: {e}",
                ) from e
            if dados.get("version") != VERSAO_MANIFESTO:
                raise IngestError(
                    "manifest_version",
                    f"{MANIFESTO} versão {dados.get('version')!r};"
                    f" esta instância lê a versão {VERSAO_MANIFESTO}",
                )
            return dados, None
    return _por_convencao(arquivos), (
        f"sem {MANIFESTO} no artifact — os anexos foram reconhecidos por nome"
        " de arquivo, e nenhum sinal foi extraído. Declare um manifesto para"
        " o pipeline poder emitir métrica sem depender de convenção."
    )


def _por_convencao(arquivos: dict[str, bytes]) -> dict[str, Any]:
    """Sem manifesto sobra reconhecer anexo por nome. Sinal, não: um número
    solto num arquivo desconhecido não tem nome nem unidade, e inventar os
    dois seria pior que não ter."""
    anexos = []
    for nome in sorted(arquivos):
        for kind, regex in CONVENCAO.items():
            if regex.search(nome):
                anexos.append({"kind": kind, "path": nome})
                break
    return {"version": VERSAO_MANIFESTO, "signals": [], "attachments": anexos}


def normalizar_sinais(manifesto: dict[str, Any], quando: str) -> list[dict[str, Any]]:
    """Sinal é `(kind, name, value, unit, at)` e nada mais.

    O Arbites NÃO conhece a semântica: ele não sabe que `lcp_ms` maior é pior.
    Direção e meta são configuração de quem instala — aqui só se guarda o
    número, para a série existir.
    """
    saida = []
    for bruto in manifesto.get("signals") or []:
        nome = str(bruto.get("name") or "").strip()
        if not nome:
            continue
        try:
            valor = float(bruto["value"])
        except (KeyError, TypeError, ValueError):
            # sinal sem número não é sinal; ignorar em silêncio seria pior,
            # mas derrubar a ingestão inteira por um item também
            continue
        saida.append({
            "kind": str(bruto.get("kind") or "custom"),
            "name": nome,
            "value": valor,
            "unit": bruto.get("unit"),
            "at": bruto.get("at") or quando,
        })
    return saida


# -- gravação ----------------------------------------------------------------


def escrever_run(
    raiz: Path, run: dict[str, Any], manifesto: dict[str, Any],
    arquivos: dict[str, bytes], aviso: str | None,
) -> dict[str, Any]:
    """Grava o run como documento do workspace + anexos ao lado.

    Idempotente por construção: o caminho vem da chave do run, então ingerir
    de novo reescreve o mesmo arquivo em vez de criar um segundo.
    """
    chave = run["key"]
    rel = caminho_do_run(chave, run.get("started_at"))
    destino = raiz / rel
    destino.parent.mkdir(parents=True, exist_ok=True)

    sinais = normalizar_sinais(manifesto, run.get("started_at") or run["ingested_at"])

    # anexos: gravados ao lado e HASHEADOS, como a evidência de execução já é
    pasta = destino.parent / chave
    anexos = []
    corpo_analise = ""
    for item in manifesto.get("attachments") or []:
        caminho = item.get("path")
        bruto = arquivos.get(caminho)
        if bruto is None:
            continue
        pasta.mkdir(parents=True, exist_ok=True)
        alvo = pasta / Path(caminho).name
        alvo.write_bytes(bruto)
        anexos.append({
            "kind": item.get("kind") or "file",
            "path": f"{rel.rsplit('/', 1)[0]}/{chave}/{alvo.name}",
            "title": item.get("title"),
            "sha256": hashlib.sha256(bruto).hexdigest(),
            "bytes": len(bruto),
        })
        # A análise que o pipeline já escreveu vira o CORPO do documento:
        # reescrevê-la seria desperdiçar trabalho que já foi feito.
        if (item.get("kind") == "analysis" or CONVENCAO["analysis"].search(caminho)) \
                and not corpo_analise:
            try:
                corpo_analise = bruto.decode("utf-8")
            except UnicodeDecodeError:
                corpo_analise = ""

    meta = {
        "id": chave,
        "provider": run["provider"],
        "repo": run["repo"],
        "workflow": run["workflow"],
        "run_id": run["run_id"],
        "event": run.get("event"),
        "conclusion": run.get("conclusion"),
        "commit": run.get("commit"),
        "branch": run.get("branch"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "url": run.get("url"),
        "ingested_at": run["ingested_at"],
        "signals": sinais,
        "attachments": anexos,
    }
    if aviso:
        meta["ingest_warning"] = aviso

    corpo = corpo_analise or _resumo(run, sinais, anexos)
    post = frontmatter.Post(corpo, **{k: v for k, v in meta.items() if v is not None})
    destino.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return {"path": rel, **meta}


def _resumo(run: dict[str, Any], sinais: list, anexos: list) -> str:
    linhas = [
        f"# {run['workflow']} — run {run['run_id']}",
        "",
        f"- Conclusão: {run.get('conclusion') or '—'}",
        f"- Disparado por: {run.get('event') or '—'}",
        f"- Commit: {run.get('commit') or '—'}",
        "",
        f"{len(sinais)} sinal(is) e {len(anexos)} anexo(s).",
    ]
    return "\n".join(linhas) + "\n"


def abrir_artifact(bruto: bytes) -> dict[str, bytes]:
    """Descompacta o artifact em memória. Arquivo grande demais não entra: um
    zip malicioso ou um print de 2 GB não pode derrubar a instância."""
    limite = 200 * 1024 * 1024
    arquivos: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(bruto)) as zf:
            total = 0
            for info in zf.infolist():
                if info.is_dir():
                    continue
                total += info.file_size
                if total > limite:
                    raise IngestError(
                        "artifact_too_large",
                        f"artifact acima de {limite // (1024 * 1024)} MB descompactado",
                    )
                arquivos[info.filename] = zf.read(info)
    except zipfile.BadZipFile as e:
        raise IngestError("artifact_invalid", f"artifact não é um zip: {e}") from e
    return arquivos


# -- orquestração ------------------------------------------------------------


def _iso(bruto: Any) -> str | None:
    if not bruto:
        return None
    return str(bruto).replace("Z", "+00:00") if str(bruto).endswith("Z") else str(bruto)


class CIIngestor:
    """Puxa do provedor os runs que ainda não estão no disco.

    Puxa (ADR 0016), não recebe: webhook exigiria que a instância local fosse
    alcançável da internet — coisa que uma ferramenta local-first não é. E o
    modelo de puxar dá de graça a retomada: quem responde "o que falta" é o
    disco, não uma inscrição que pode ter perdido eventos enquanto a máquina
    estava desligada.
    """

    def __init__(self, ws, conn, client) -> None:
        self.ws = ws
        self.conn = conn
        self.client = client

    # -- marca d'água ------------------------------------------------------

    def ja_ingeridos(self) -> set[str]:
        """As chaves que já têm arquivo. ESTA é a marca d'água.

        Derivada, não guardada: um contador "último run visto" mente na
        primeira falha no meio (guardei 120, mas o 118 falhou o download) e
        aquele run fica perdido para sempre. Perguntar ao disco não mente.
        """
        base = self.ws.root / "ci"
        if not base.exists():
            return set()
        return {p.stem for p in base.rglob("*.md")}

    # -- fontes ------------------------------------------------------------

    def fontes(self) -> list[dict[str, Any]]:
        bruto = (self.ws.config().get("observability") or {}).get("sources") or []
        fontes = []
        for item in bruto:
            if not item.get("repo"):
                continue
            fontes.append({
                "provider": item.get("provider", "github"),
                "repo": item["repo"],
                "workflow": item.get("workflow"),
                "artifact": item.get("artifact"),
            })
        return fontes

    # -- ingestão ----------------------------------------------------------

    def ingerir(self, limite: int | None = None) -> dict[str, Any]:
        config = self.ws.config().get("observability") or {}
        limite = limite or int(config.get("max_runs_per_poll") or 50)
        fontes = self.fontes()
        if not fontes:
            raise IngestError(
                "no_sources",
                "nenhuma fonte de observabilidade em arbites.yaml"
                " (observability.sources)",
            )
        resumo: dict[str, Any] = {"ingested": [], "skipped": 0, "errors": []}
        for fonte in fontes:
            self._ingerir_fonte(fonte, limite, resumo)
        return resumo

    def _pendentes(self, fonte: dict, limite: int) -> list[dict]:
        """Percorre as páginas do provedor até só encontrar run já ingerido.

        Parar na primeira página conhecida seria errado quando a instância
        ficou dias fora: o intervalo perdido está DEPOIS dela.
        """
        vistos = self.ja_ingeridos()
        pendentes: list[dict] = []
        pagina = 1
        while len(pendentes) < limite and pagina <= 10:
            lote = self.client.list_workflow_runs(
                fonte["repo"], fonte.get("workflow"), page=pagina, per_page=50,
            )
            if not lote:
                break
            novos_na_pagina = 0
            for bruto in lote:
                chave = run_key(fonte["provider"], bruto.get("id"))
                if chave in vistos:
                    continue
                novos_na_pagina += 1
                pendentes.append(bruto)
                if len(pendentes) >= limite:
                    break
            if novos_na_pagina == 0:
                break  # página inteira já conhecida: o passado está coberto
            pagina += 1
        # do mais velho para o mais novo: a série temporal nasce em ordem
        pendentes.reverse()
        return pendentes

    def _ingerir_fonte(self, fonte: dict, limite: int, resumo: dict) -> None:
        from .ci import CIError
        from .indexer import reindex_file

        try:
            pendentes = self._pendentes(fonte, limite)
        except CIError as e:
            resumo["errors"].append({"repo": fonte["repo"], "code": e.code,
                                     "message": e.message})
            return

        for bruto in pendentes:
            chave = run_key(fonte["provider"], bruto.get("id"))
            try:
                gravado = self._ingerir_run(fonte, bruto, chave)
            except CIError as e:
                # Limite de taxa ou queda no meio NÃO perde run: a marca
                # d'água é o disco, então a próxima chamada recomeça daqui.
                resumo["errors"].append({"run": chave, "code": e.code,
                                         "message": e.message})
                resumo["stopped"] = "rate_limited" if e.code in (
                    "rate_limited", "github_error") else e.code
                return
            except IngestError as e:
                # Artifact quebrado é problema DAQUELE run, não da ingestão:
                # registra e segue, senão um zip corrompido trava a série.
                resumo["errors"].append({"run": chave, "code": e.code,
                                         "message": e.message})
                continue
            reindex_file(self.ws, self.conn, self.ws.root / gravado["path"])
            resumo["ingested"].append(gravado["id"])

    def _ingerir_run(self, fonte: dict, bruto: dict, chave: str) -> dict[str, Any]:
        run = {
            "key": chave,
            "provider": fonte["provider"],
            "repo": fonte["repo"],
            "workflow": bruto.get("name") or fonte.get("workflow") or "—",
            "run_id": str(bruto.get("id")),
            "event": bruto.get("event"),
            "conclusion": bruto.get("conclusion"),
            "commit": bruto.get("head_sha"),
            "branch": bruto.get("head_branch"),
            "started_at": _iso(bruto.get("run_started_at") or bruto.get("created_at")),
            "finished_at": _iso(bruto.get("updated_at")),
            "url": bruto.get("html_url"),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        arquivos = self._baixar_artifacts(fonte, bruto.get("id"))
        manifesto, aviso = ler_manifesto(arquivos)
        return escrever_run(self.ws.root, run, manifesto, arquivos, aviso)

    def _baixar_artifacts(self, fonte: dict, run_id: Any) -> dict[str, bytes]:
        desejado = fonte.get("artifact")
        arquivos: dict[str, bytes] = {}
        for artifact in self.client.list_artifacts(fonte["repo"], run_id):
            if desejado and artifact.get("name") != desejado:
                continue
            if artifact.get("expired"):
                continue  # o GitHub apaga artifact por retenção; não é erro
            bruto = self.client.download_artifact(fonte["repo"], artifact["id"])
            arquivos.update(abrir_artifact(bruto))
        return arquivos


# -- consulta ----------------------------------------------------------------


def listar_runs(conn, limite: int = 50, workflow: str | None = None) -> list[dict]:
    sql = "SELECT * FROM ci_runs"
    args: list[Any] = []
    if workflow:
        sql += " WHERE workflow = ?"
        args.append(workflow)
    sql += " ORDER BY COALESCE(started_at, ingested_at) DESC LIMIT ?"
    args.append(limite)
    saida = []
    for row in conn.execute(sql, args):
        item = dict(row)
        item["signals"] = [
            dict(s) for s in conn.execute(
                "SELECT kind, name, value, unit, at FROM ci_signals"
                " WHERE run_id = ? ORDER BY name", (row["id"],),
            )
        ]
        item["attachments"] = [
            dict(a) for a in conn.execute(
                "SELECT kind, path, title, sha256, bytes FROM ci_attachments"
                " WHERE run_id = ? ORDER BY kind, path", (row["id"],),
            )
        ]
        saida.append(item)
    return saida


def serie(conn, name: str, since: str | None = None,
          until: str | None = None) -> dict[str, Any]:
    """A série de UM sinal no tempo — o eixo que faz um dashboard virar
    observabilidade: não "quantos passaram hoje", e sim "está piorando?"."""
    sql = (
        "SELECT s.at, s.value, s.unit, s.kind, s.run_id, r.conclusion, r.url"
        " FROM ci_signals s LEFT JOIN ci_runs r ON r.id = s.run_id"
        " WHERE s.name = ?"
    )
    args: list[Any] = [name]
    if since:
        sql += " AND s.at >= ?"
        args.append(since)
    if until:
        sql += " AND s.at <= ?"
        args.append(until)
    sql += " ORDER BY s.at"
    pontos = [dict(r) for r in conn.execute(sql, args)]
    return {"name": name, "points": pontos, "count": len(pontos)}


def nomes_de_sinal(conn) -> list[dict[str, Any]]:
    return [
        dict(r) for r in conn.execute(
            "SELECT name, kind, unit, COUNT(*) AS points,"
            " MAX(at) AS last_at, MIN(at) AS first_at"
            " FROM ci_signals GROUP BY name, kind, unit ORDER BY name"
        )
    ]
