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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import frontmatter

MANIFESTO = "arbites.json"
# Versão 2 acrescenta `labels` (qual componente/ambiente o run validou) e
# `findings` (achado estruturado, p. ex. WCAG). A 1 continua válida: um
# manifesto antigo não pode parar de ser lido porque o formato cresceu
# (change 0175).
VERSAO_MANIFESTO = 2
VERSOES_ACEITAS = (1, 2)

# Convenção de nome — o FALLBACK, para quando o workflow não pode ser
# alterado. Anunciado como fallback de propósito: ele acerta hoje e quebra
# calado no dia em que alguém renomear o arquivo.
CONVENCAO = {
    "analysis": re.compile(r"(analysis|analise|relatorio)\.md$", re.I),
    "axe": re.compile(r"(axe|a11y|acessibilidade)[^/]*\.json$", re.I),
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
            if dados.get("version") not in VERSOES_ACEITAS:
                raise IngestError(
                    "manifest_version",
                    f"{MANIFESTO} versão {dados.get('version')!r};"
                    f" esta instância lê as versões"
                    f" {', '.join(str(v) for v in VERSOES_ACEITAS)}",
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


def normalizar_rotulos(manifesto: dict[str, Any]) -> dict[str, str]:
    """`labels` do manifesto: o que ESTE run validou (change 0175).

    O repositório onde o workflow mora não é o que está sob teste. Num
    projeto de micro-frontends o mesmo repositório de testes valida vários
    componentes, e vários repositórios de deploy chamam a mesma suíte — sem
    um rótulo declarado, a taxa de sucesso vira uma média de coisas
    diferentes, que não é a saúde de nada.

    Chave livre de propósito: a topologia é de quem instala, e fixar
    `componente`/`ambiente` no código só obrigaria a contorná-los depois.
    """
    bruto = manifesto.get("labels") or {}
    if not isinstance(bruto, dict):
        return {}
    saida = {}
    for chave, valor in bruto.items():
        nome = str(chave).strip()
        if not nome or valor is None:
            continue
        texto = str(valor).strip()
        if texto:
            saida[nome] = texto[:120]
    return saida


def extrair_achados(manifesto: dict[str, Any],
                    arquivos: dict[str, bytes]) -> list[dict[str, Any]]:
    """Achados estruturados: os declarados no manifesto mais os lidos do axe.

    Duas entradas, uma forma só. O anexo `kind: "axe"` é o caminho curto —
    o pipeline publica o JSON que a ferramenta já produz, sem reescrever
    nada — e `findings` no manifesto atende quem usa outra ferramenta.
    """
    from .ci_axe import ler_axe, normalizar_achados

    saida = normalizar_achados(manifesto.get("findings"))
    caminhos = [
        item.get("path") for item in (manifesto.get("attachments") or [])
        if item.get("kind") == "axe" and item.get("path")
    ]
    if not caminhos:
        caminhos = [n for n in arquivos if CONVENCAO["axe"].search(n)]
    for caminho in caminhos:
        bruto = arquivos.get(caminho)
        if bruto is not None:
            saida.extend(ler_axe(bruto))
    return saida


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


def extrair_cenarios(manifesto: dict[str, Any],
                     arquivos: dict[str, bytes]) -> list[dict[str, Any]]:
    """Resultado POR CENÁRIO, do Cucumber JSON que já vem no artifact.

    O manifesto declara MEDIDA agregada — "2 cenários falharam" — e isso não
    responde *qual* virou instável. Instabilidade é por cenário: um teste que
    passa, falha e passa de novo não aparece em nenhuma média, e é justamente
    o que corrói a confiança na suíte.

    Reaproveita o leitor da change 0148: ter dois parsers para o mesmo formato
    é convidar a divergência.
    """
    from .integrations_file import ArquivoErro, ler_cucumber

    caminhos = [
        item.get("path") for item in (manifesto.get("attachments") or [])
        if item.get("kind") == "cucumber" and item.get("path")
    ]
    if not caminhos:
        caminhos = [n for n in arquivos if CONVENCAO["cucumber"].search(n)]

    saida: list[dict[str, Any]] = []
    for caminho in caminhos:
        bruto = arquivos.get(caminho)
        if bruto is None:
            continue
        try:
            cenarios = ler_cucumber(bruto)
        except ArquivoErro:
            continue  # artifact quebrado é problema daquele run, não da série
        for cenario in cenarios:
            saida.append({
                "scenario": cenario.get("scenario"),
                "feature": cenario.get("feature"),
                "testcase_id": cenario.get("testcase_id"),
                "status": cenario.get("status"),
            })
    return saida


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
        "jobs": run.get("jobs") or [],
        "scenarios": extrair_cenarios(manifesto, arquivos),
        "labels": normalizar_rotulos(manifesto),
        "findings": extrair_achados(manifesto, arquivos),
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

    @staticmethod
    def _motivo_da_parada(code: str) -> str:
        """"Parado por credencial" e "sem run novo" parecem iguais na tela —
        nenhum dado novo — e pedem ações opostas (change 0157)."""
        if code == "bad_credential":
            return "bad_credential"
        return "rate_limited" if code in ("rate_limited", "github_error") else code

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
            resumo["stopped"] = self._motivo_da_parada(e.code)
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
                resumo["stopped"] = self._motivo_da_parada(e.code)
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
        # jobs: é o degrau do meio da descida (gráfico → run → job → anexo).
        # Sem ele "o pico foi em quê?" morre em "foi neste run", que é onde
        # um mural de gráficos costuma parar.
        run["jobs"] = self._jobs(fonte, bruto.get("id"))
        arquivos = self._baixar_artifacts(fonte, bruto.get("id"))
        manifesto, aviso = ler_manifesto(arquivos)
        return escrever_run(self.ws.root, run, manifesto, arquivos, aviso)

    def _jobs(self, fonte: dict, run_id: Any) -> list[dict[str, Any]]:
        from .ci import CIError

        try:
            bruto = self.client.get_jobs(fonte["repo"], run_id)
        except CIError:
            return []  # job é detalhe; sem ele o run ainda vale
        return [
            {
                "name": j.get("name"),
                "conclusion": j.get("conclusion"),
                "started_at": _iso(j.get("started_at")),
                "finished_at": _iso(j.get("completed_at")),
                "url": j.get("html_url"),
            }
            for j in bruto or []
        ]

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


def _jobs_de(conn, run_id: str) -> list[dict]:
    return [
        dict(j) for j in conn.execute(
            "SELECT name, conclusion, started_at, finished_at, url FROM ci_jobs"
            " WHERE run_id = ? ORDER BY ord", (run_id,),
        )
    ]


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
        item["jobs"] = _jobs_de(conn, row["id"])
        saida.append(item)
    return saida


def run_detalhado(ws, conn, run_id: str) -> dict[str, Any]:
    """Um run com o CORPO: a análise que o pipeline escreveu, renderizada na
    tela ao lado dos sinais em vez de reescrita aqui."""
    row = conn.execute("SELECT * FROM ci_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise IngestError("not_found", f"run {run_id} não ingerido")
    item = dict(row)
    item["signals"] = [
        dict(s) for s in conn.execute(
            "SELECT kind, name, value, unit, at FROM ci_signals"
            " WHERE run_id = ? ORDER BY name", (run_id,))
    ]
    item["attachments"] = [
        dict(a) for a in conn.execute(
            "SELECT kind, path, title, sha256, bytes FROM ci_attachments"
            " WHERE run_id = ? ORDER BY kind, path", (run_id,))
    ]
    item["jobs"] = _jobs_de(conn, run_id)
    caminho = ws.root / row["path"]
    item["analysis"] = (
        frontmatter.loads(caminho.read_text(encoding="utf-8")).content
        if caminho.exists() else ""
    )
    return item


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


# -- o painel de observabilidade (change 0155) -------------------------------
#
# A diferença para o Dashboard não é o nome, é o EIXO. O Dashboard responde
# "como está agora" — retrato. Aqui a pergunta é "o que mudou, quando e por
# quê", e por isso toda resposta vem com o período anterior ao lado: um número
# sozinho não diz se está melhorando.


def _dias_atras(dias: int) -> tuple[str, str, str]:
    fim = datetime.now(timezone.utc)
    inicio = fim - timedelta(days=dias)
    anterior = inicio - timedelta(days=dias)
    return anterior.isoformat(), inicio.isoformat(), fim.isoformat()


def _metas(ws) -> dict[str, dict[str, Any]]:
    """Meta e direção são CONFIGURAÇÃO de quem instala, não semântica no
    código: o Arbites não tem como saber que `lcp_ms` maior é pior, nem qual
    número é aceitável neste produto."""
    bruto = (ws.config().get("observability") or {}).get("goals") or {}
    saida = {}
    for nome, spec in bruto.items():
        if not isinstance(spec, dict):
            continue
        saida[str(nome)] = {
            "direction": spec.get("direction"),  # "lower" | "higher"
            "goal": spec.get("goal"),
        }
    return saida


def _media(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 3) if valores else None


def _variacao(atual: float | None, antes: float | None) -> float | None:
    if atual is None or antes in (None, 0):
        return None
    return round((atual - antes) / abs(antes) * 100, 1)


def painel(ws, conn, dias: int = 30) -> dict[str, Any]:
    inicio_anterior, inicio, fim = _dias_atras(dias)
    metas = _metas(ws)

    def runs_entre(a: str, b: str) -> list[dict]:
        return [
            dict(r) for r in conn.execute(
                "SELECT id, workflow, conclusion, started_at, url, ingest_warning"
                " FROM ci_runs WHERE COALESCE(started_at, ingested_at) >= ?"
                " AND COALESCE(started_at, ingested_at) < ? ORDER BY"
                " COALESCE(started_at, ingested_at)", (a, b),
            )
        ]

    atuais, anteriores = runs_entre(inicio, fim), runs_entre(inicio_anterior, inicio)

    def taxa(runs: list[dict]) -> float | None:
        if not runs:
            return None
        ok = sum(1 for r in runs if r["conclusion"] == "success")
        return round(ok / len(runs) * 100, 1)

    ultimo = conn.execute(
        "SELECT COALESCE(started_at, ingested_at) AS at FROM ci_runs"
        " ORDER BY 1 DESC LIMIT 1"
    ).fetchone()
    silencio = None
    if ultimo and ultimo["at"]:
        try:
            silencio = (datetime.now(timezone.utc) - datetime.fromisoformat(
                ultimo["at"])).days
        except ValueError:
            silencio = None

    saude = {
        "runs": len(atuais), "runs_previous": len(anteriores),
        "success_rate": taxa(atuais), "success_rate_previous": taxa(anteriores),
        "last_run_at": ultimo["at"] if ultimo else None,
        "days_since_last_run": silencio,
        # "87% contra a meta de 95%" — declarado, não inferido
        "goal": (metas.get("success_rate") or {}).get("goal"),
    }

    # -- sinais: a série e o que ela fez em relação ao período anterior -----
    sinais = []
    for linha in conn.execute(
        "SELECT name, kind, unit FROM ci_signals GROUP BY name, kind, unit"
        " ORDER BY name"
    ):
        nome = linha["name"]
        pontos = [
            dict(p) for p in conn.execute(
                "SELECT s.at, s.value, s.run_id, r.conclusion, r.url"
                " FROM ci_signals s LEFT JOIN ci_runs r ON r.id = s.run_id"
                " WHERE s.name = ? AND s.at >= ? AND s.at < ? ORDER BY s.at",
                (nome, inicio, fim),
            )
        ]
        antes = [
            r["value"] for r in conn.execute(
                "SELECT value FROM ci_signals WHERE name = ? AND at >= ? AND at < ?",
                (nome, inicio_anterior, inicio),
            )
        ]
        media_atual = _media([p["value"] for p in pontos])
        media_antes = _media(antes)
        meta = metas.get(nome) or {}
        sinais.append({
            "name": nome, "kind": linha["kind"], "unit": linha["unit"],
            "points": pontos,
            "current": pontos[-1]["value"] if pontos else None,
            "average": media_atual, "previous_average": media_antes,
            "delta_pct": _variacao(media_atual, media_antes),
            "direction": meta.get("direction"), "goal": meta.get("goal"),
        })

    instaveis = instabilidade(conn, inicio_anterior, inicio, fim)
    # Recortes: num projeto de micro-frontends a média global esconde
    # exatamente o que se quer ver (change 0175). O rótulo em destaque é o
    # mais usado pelos runs — quem instala escolhe a topologia, não o código.
    rotulos = nomes_de_rotulo(conn)
    recortes = {
        nome: por_rotulo(conn, nome, inicio_anterior, inicio, fim)
        for nome in rotulos[:4]
    }
    return {
        "period": {"since": inicio, "until": fim, "days": dias},
        "previous": {"since": inicio_anterior, "until": inicio},
        "health": saude,
        "signals": sinais,
        "flaky": instaveis,
        "changes": _o_que_mudou(atuais, anteriores, sinais, saude, instaveis),
        "runs": listar_runs(conn, 30),
        "distribution": distribuicao(conn, inicio, fim),
        "findings": achados(conn, inicio_anterior, inicio, fim),
        "by_repo": por_repositorio(conn, inicio_anterior, inicio, fim),
        "label_names": rotulos,
        "by_label": recortes,
    }


def _fatias(pares: list[tuple[str, int]], ordem: tuple[str, ...] = ()) -> list[dict]:
    """Fatias de uma pizza, com o total junto.

    A porcentagem vai calculada no servidor: duas telas dividindo o mesmo
    número por conta própria acabam discordando no arredondamento.
    """
    total = sum(v for _, v in pares) or 0
    def chave(item: tuple[str, int]) -> tuple:
        rotulo, valor = item
        return (ordem.index(rotulo) if rotulo in ordem else len(ordem), -valor)
    return [
        {"label": rotulo, "value": valor,
         "pct": round(valor / total * 100, 1) if total else 0.0}
        for rotulo, valor in sorted(pares, key=chave) if valor
    ]


def distribuicao(conn, inicio: str, fim: str) -> dict[str, Any]:
    """Como as execuções do período se dividem — é a pizza que o mural pede.

    Série responde "está piorando?"; divisão responde "de que é feito o
    período". As duas perguntas são diferentes e nenhuma substitui a outra.
    """
    conclusoes = [
        (r["conclusion"] or "sem conclusão", r["c"]) for r in conn.execute(
            "SELECT conclusion, COUNT(*) c FROM ci_runs"
            " WHERE COALESCE(started_at, ingested_at) >= ?"
            " AND COALESCE(started_at, ingested_at) < ? GROUP BY conclusion",
            (inicio, fim))
    ]
    cenarios = [
        (r["status"] or "sem status", r["c"]) for r in conn.execute(
            "SELECT status, COUNT(*) c FROM ci_scenarios"
            " WHERE at >= ? AND at < ? GROUP BY status", (inicio, fim))
    ]
    return {
        "runs_by_conclusion": _fatias(
            conclusoes, ("success", "failure", "cancelled", "timed_out")),
        "scenarios_by_status": _fatias(
            cenarios, ("passed", "failed", "blocked", "skipped")),
    }


def achados(conn, inicio_anterior: str, inicio: str, fim: str) -> dict[str, Any]:
    """Acessibilidade e afins, agregados — por gravidade, regra e critério.

    `violacoes_axe: 14` diz que piorou, não diz o quê. Aqui o número vira
    trabalho priorizável: quantos elementos, de que gravidade, contra qual
    critério da WCAG, em que página.
    """
    def soma(desde: str, ate: str) -> int:
        linha = conn.execute(
            "SELECT COALESCE(SUM(count), 0) t FROM ci_findings"
            " WHERE at >= ? AND at < ?", (desde, ate)).fetchone()
        return int(linha["t"] or 0)

    por_impacto = [
        (r["impact"] or "unknown", int(r["t"] or 0)) for r in conn.execute(
            "SELECT impact, SUM(count) t FROM ci_findings"
            " WHERE at >= ? AND at < ? GROUP BY impact", (inicio, fim))
    ]
    por_categoria = [
        (r["category"] or "quality", int(r["t"] or 0)) for r in conn.execute(
            "SELECT category, SUM(count) t FROM ci_findings"
            " WHERE at >= ? AND at < ? GROUP BY category", (inicio, fim))
    ]
    regras = [
        {"rule": r["rule"], "impact": r["impact"], "wcag": r["wcag"],
         "level": r["level"], "count": int(r["t"] or 0), "runs": r["runs"],
         "help": r["help"], "help_url": r["help_url"]}
        for r in conn.execute(
            "SELECT rule, impact, wcag, level, SUM(count) t,"
            " COUNT(DISTINCT run_id) runs, MAX(help) help, MAX(help_url) help_url"
            " FROM ci_findings WHERE at >= ? AND at < ?"
            " GROUP BY rule ORDER BY t DESC LIMIT 12", (inicio, fim))
    ]
    criterios = [
        {"wcag": r["wcag"], "level": r["level"], "count": int(r["t"] or 0)}
        for r in conn.execute(
            "SELECT wcag, MAX(level) level, SUM(count) t FROM ci_findings"
            " WHERE at >= ? AND at < ? AND wcag IS NOT NULL"
            " GROUP BY wcag ORDER BY t DESC LIMIT 12", (inicio, fim))
    ]
    paginas = [
        {"page": r["page"], "count": int(r["t"] or 0)}
        for r in conn.execute(
            "SELECT page, SUM(count) t FROM ci_findings"
            " WHERE at >= ? AND at < ? AND page IS NOT NULL AND page != ''"
            " GROUP BY page ORDER BY t DESC LIMIT 10", (inicio, fim))
    ]
    atual, antes = soma(inicio, fim), soma(inicio_anterior, inicio)
    return {
        "total": atual, "previous_total": antes,
        "delta_pct": _variacao(float(atual), float(antes) if antes else None),
        "by_impact": _fatias(por_impacto, ("critical", "serious", "moderate",
                                           "minor", "unknown")),
        "by_category": _fatias(por_categoria),
        "top_rules": regras,
        "by_wcag": criterios,
        "top_pages": paginas,
    }


def _recorte(conn, coluna: str, tabela: str, inicio_anterior: str,
             inicio: str, fim: str, filtro: str = "", args: tuple = ()) -> list[dict]:
    """Saúde de cada valor de um recorte (repositório ou rótulo).

    Num projeto de micro-frontends a média global não é a saúde de nada: oito
    componentes atrás de uma taxa só escondem exatamente o que se quer ver.
    """
    def linhas(desde: str, ate: str) -> dict[str, dict]:
        sql = (
            f"SELECT {coluna} AS chave,"
            " SUM(CASE WHEN r.conclusion = 'success' THEN 1 ELSE 0 END) ok,"
            " COUNT(*) total, MAX(COALESCE(r.started_at, r.ingested_at)) ultimo"
            f" FROM {tabela} WHERE COALESCE(r.started_at, r.ingested_at) >= ?"
            " AND COALESCE(r.started_at, r.ingested_at) < ?"
            + (f" AND {filtro}" if filtro else "")
            + f" GROUP BY {coluna}"
        )
        return {
            r["chave"]: {"runs": r["total"], "ok": r["ok"], "last_run_at": r["ultimo"]}
            for r in conn.execute(sql, (desde, ate, *args)) if r["chave"]
        }

    agora, antes = linhas(inicio, fim), linhas(inicio_anterior, inicio)
    saida = []
    for chave, dados in agora.items():
        taxa = round(dados["ok"] / dados["runs"] * 100, 1) if dados["runs"] else None
        anterior = antes.get(chave)
        taxa_antes = (round(anterior["ok"] / anterior["runs"] * 100, 1)
                      if anterior and anterior["runs"] else None)
        saida.append({
            "name": chave, "runs": dados["runs"],
            "failures": dados["runs"] - dados["ok"],
            "success_rate": taxa, "success_rate_previous": taxa_antes,
            "delta_pct": _variacao(taxa, taxa_antes),
            "last_run_at": dados["last_run_at"],
        })
    # pior primeiro: quem olha o painel quer saber onde doer
    saida.sort(key=lambda x: (x["success_rate"] if x["success_rate"] is not None
                              else 101, -x["runs"]))
    return saida


def por_repositorio(conn, inicio_anterior: str, inicio: str,
                    fim: str) -> list[dict[str, Any]]:
    return _recorte(conn, "r.repo", "ci_runs r", inicio_anterior, inicio, fim)


# Acima disto um rótulo deixa de ser recorte e vira identificador: `versao`
# com 24 valores não agrupa nada, só empurra `componente` para fora da tela.
MAX_VALORES_DE_ROTULO = 12


def nomes_de_rotulo(conn) -> list[str]:
    """Rótulos que servem como RECORTE, do mais grosso para o mais fino.

    Ordenados por número de valores distintos: `stack` (2) antes de
    `componente` (8), e `versao` (dezenas) fora — um rótulo com um valor por
    run não agrupa nada. Dois valores no mínimo, porque um só não divide.
    """
    return [
        r["name"] for r in conn.execute(
            "SELECT name, COUNT(DISTINCT value) v FROM ci_labels"
            " GROUP BY name HAVING v BETWEEN 2 AND ? ORDER BY v, name",
            (MAX_VALORES_DE_ROTULO,),
        )
    ]


def por_rotulo(conn, rotulo: str, inicio_anterior: str, inicio: str,
               fim: str) -> list[dict[str, Any]]:
    return _recorte(
        conn, "l.value", "ci_labels l JOIN ci_runs r ON r.id = l.run_id",
        inicio_anterior, inicio, fim, "l.name = ?", (rotulo,),
    )


def instabilidade(conn, inicio_anterior: str, inicio: str,
                  fim: str) -> list[dict[str, Any]]:
    """Cenários que passam E falham no mesmo período — e se isso é NOVO.

    Instabilidade não aparece em média nenhuma: um teste que passa, falha e
    passa de novo some numa taxa de sucesso e continua corroendo a confiança
    na suíte. E "instável" sozinho não é notícia — quem já sabe que aquele
    teste balança não precisa ser lembrado. A notícia é **virou** instável:
    estava estável no período anterior e não está mais.
    """
    def por_cenario(desde: str, ate: str) -> dict[str, dict[str, Any]]:
        saida: dict[str, dict[str, Any]] = {}
        for linha in conn.execute(
            "SELECT scenario, testcase_id, status, run_id, at FROM ci_scenarios"
            " WHERE at >= ? AND at < ? ORDER BY at", (desde, ate),
        ):
            item = saida.setdefault(linha["scenario"], {
                "scenario": linha["scenario"],
                "testcase_id": linha["testcase_id"],
                "statuses": [], "runs": [],
            })
            item["statuses"].append(linha["status"])
            item["runs"].append(linha["run_id"])
            if linha["testcase_id"] and not item["testcase_id"]:
                item["testcase_id"] = linha["testcase_id"]
        return saida

    agora = por_cenario(inicio, fim)
    antes = por_cenario(inicio_anterior, inicio)

    def balanca(item: dict[str, Any] | None) -> bool:
        if not item:
            return False
        estados = set(item["statuses"])
        return "passed" in estados and bool(estados & {"failed", "blocked"})

    saida = []
    for nome, item in sorted(agora.items()):
        if not balanca(item):
            continue
        anterior = antes.get(nome)
        viradas = sum(
            1 for a, b in zip(item["statuses"], item["statuses"][1:]) if a != b
        )
        saida.append({
            "scenario": nome,
            "testcase_id": item["testcase_id"],
            "runs": len(item["statuses"]),
            "failures": sum(1 for s in item["statuses"]
                            if s in ("failed", "blocked")),
            "flips": viradas,
            # a distinção que separa notícia de ruído
            "newly_flaky": not balanca(anterior),
            "last_run": item["runs"][-1] if item["runs"] else None,
        })
    return saida


def _o_que_mudou(atuais: list[dict], anteriores: list[dict],
                 sinais: list[dict], saude: dict,
                 instaveis: list[dict] | None = None) -> list[dict[str, Any]]:
    """O bloco que justifica a aba existir: o que mudou SOZINHO.

    Um mural de gráficos obriga a pessoa a caçar a diferença olhando. Aqui a
    diferença é calculada e dita em uma frase — e cada item aponta o run, para
    a descida continuar de onde a frase parou.
    """
    def plural(n: int, singular: str, plural_: str) -> str:
        return f"{n} {singular if n == 1 else plural_}"

    mudancas: list[dict[str, Any]] = []

    # 1. a ingestão emudeceu: período sem run não é "semana tranquila"
    if saude["days_since_last_run"] is not None and saude["days_since_last_run"] >= 3:
        mudancas.append({
            "kind": "silence",
            "text": f"nenhum run há {plural(saude['days_since_last_run'], 'dia', 'dias')} —"
                    " verifique o agendamento e a credencial antes de ler isto"
                    " como semana tranquila",
        })

    # 2. o run mais recente quebrou depois de uma sequência verde
    if atuais and atuais[-1]["conclusion"] not in ("success", None):
        verdes = 0
        for run in reversed(atuais[:-1]):
            if run["conclusion"] == "success":
                verdes += 1
            else:
                break
        if verdes:
            mudancas.append({
                "kind": "broke",
                "run_id": atuais[-1]["id"],
                "text": f"{atuais[-1]['workflow']} quebrou depois de"
                        f" {plural(verdes, 'execução verde', 'execuções verdes')}"
                        " seguidas",
            })

    # 3. sinal que se moveu mais de 10% contra o período anterior
    for sinal in sinais:
        variacao = sinal["delta_pct"]
        if variacao is None or abs(variacao) < 10:
            continue
        direcao = sinal["direction"]
        if direcao == "lower":
            palavra = "piorou" if variacao > 0 else "melhorou"
        elif direcao == "higher":
            palavra = "melhorou" if variacao > 0 else "piorou"
        else:
            # sem direção declarada o Arbites NÃO julga: diz que mudou
            palavra = "subiu" if variacao > 0 else "caiu"
        unidade = f" {sinal['unit']}" if sinal["unit"] else ""
        mudancas.append({
            "kind": "signal",
            "signal": sinal["name"],
            "text": f"{sinal['name']} {palavra} {abs(variacao)}%"
                    f" ({sinal['previous_average']}{unidade} →"
                    f" {sinal['average']}{unidade}) contra o período anterior",
            "goal_miss": (
                sinal["goal"] is not None and sinal["average"] is not None
                and ((direcao == "lower" and sinal["average"] > sinal["goal"])
                     or (direcao == "higher" and sinal["average"] < sinal["goal"]))
            ),
        })

    # 4. teste que VIROU instável: o que estava estável e passou a balançar.
    # "Está instável" não é notícia para quem já sabe; "virou" é.
    for item in instaveis or []:
        if not item["newly_flaky"]:
            continue
        alvo = item["testcase_id"] or item["scenario"]
        mudancas.append({
            "kind": "flaky",
            "scenario": item["scenario"],
            "testcase_id": item["testcase_id"],
            "run_id": item["last_run"],
            "text": f"{alvo} virou instável: passou e falhou em"
                    f" {plural(item['runs'], 'execução', 'execuções')} deste"
                    f" período ({plural(item['failures'], 'falha', 'falhas')},"
                    f" {plural(item['flips'], 'virada', 'viradas')})."
                    " No período anterior ele não"
                    " balançava.",
        })

    # 5. run ingerido sem manifesto: o dado existe mas veio por convenção
    sem_manifesto = [r for r in atuais if r.get("ingest_warning")]
    if sem_manifesto:
        mudancas.append({
            "kind": "convention",
            "run_id": sem_manifesto[-1]["id"],
            "text": (
                f"{len(sem_manifesto)} "
                + ("execução do período chegou" if len(sem_manifesto) == 1
                   else "execuções do período chegaram")
                + f" sem {MANIFESTO} — os anexos vieram por convenção de nome"
                  " e nenhum sinal foi extraído"
            ),
        })
    return mudancas
