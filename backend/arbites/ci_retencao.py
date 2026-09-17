"""Retenção de artefato e sinal de CI (change 0156).

## O problema é aritmética, não hipótese

Um cron diário com prints enche disco. Trinta prints por run, um run por dia:
em um ano são mais de dez mil arquivos que ninguém vai abrir. Esta change
decide a retenção **junto** com a ingestão — deixar para depois é exatamente
como se descobre o problema tarde.

## A regra: sinal e anexo têm valores de vida diferentes

- **Sinal** é barato (um número numa linha) e é o que FAZ a série temporal.
  Guarda-se por muito tempo — dois anos por padrão.
- **Anexo** (print, log, artifact bruto) é caro e só interessa perto do
  evento: quem olha um print de três meses atrás é raro, e quem olha uma
  série de três meses atrás é o uso normal da tela. Guarda-se por pouco —
  noventa dias por padrão — e some primeiro.

A consequência é o trade-off certo: a série continua respondendo "a
acessibilidade regrediu em agosto?" muito depois do print daquele dia ter
ido embora.

## Duas garantias que não são negociáveis

**Prévia antes de levar.** A tela mostra o que a limpeza removeria ANTES de
remover. Limpeza que só conta o que fez depois de feita obriga a confiar sem
poder conferir.

**Lixeira, não `rm`.** O removido vai para `.arbites/trash/` como todo o
resto do produto, e volta enquanto a lixeira não for esvaziada.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import frontmatter

# Padrões explícitos e com motivo escrito, não número escondido no código.
PADRAO_SINAIS_DIAS = 730     # dois anos: comparação ano a ano ainda responde
PADRAO_ANEXOS_DIAS = 90      # um trimestre: além disso, quase ninguém abre


def janelas(ws) -> dict[str, int]:
    bruto = (ws.config().get("observability") or {}).get("retention") or {}
    def ler(chave: str, padrao: int) -> int:
        try:
            valor = int(bruto.get(chave, padrao))
        except (TypeError, ValueError):
            return padrao
        return valor if valor > 0 else padrao
    return {
        "signals_days": ler("signals_days", PADRAO_SINAIS_DIAS),
        "attachments_days": ler("attachments_days", PADRAO_ANEXOS_DIAS),
    }


def _bytes_de(caminho: Path) -> int:
    if caminho.is_file():
        return caminho.stat().st_size
    return sum(p.stat().st_size for p in caminho.rglob("*") if p.is_file())


def _quando(doc: dict[str, Any]) -> datetime | None:
    bruto = doc.get("started_at") or doc.get("ingested_at")
    if not bruto:
        return None
    try:
        valor = datetime.fromisoformat(str(bruto))
    except ValueError:
        return None
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def _runs(ws) -> list[tuple[Path, dict[str, Any]]]:
    base = ws.root / "ci"
    if not base.exists():
        return []
    saida = []
    for caminho in sorted(base.rglob("*.md")):
        if len(ws.relpath(caminho).split("/")) != 3:
            continue  # `.md` mais fundo é anexo (a análise), não um run
        try:
            doc = frontmatter.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        saida.append((caminho, dict(doc.metadata)))
    return saida


def previa(ws) -> dict[str, Any]:
    """O que está ocupado e o que a próxima limpeza levaria — antes de levar."""
    conf = janelas(ws)
    agora = datetime.now(timezone.utc)
    corte_anexo = agora - timedelta(days=conf["attachments_days"])
    corte_sinal = agora - timedelta(days=conf["signals_days"])

    total_docs = total_anexos = 0
    anexos_a_remover: list[dict[str, Any]] = []
    runs_a_remover: list[dict[str, Any]] = []

    for caminho, meta in _runs(ws):
        total_docs += caminho.stat().st_size
        pasta = caminho.parent / caminho.stem
        tamanho_anexos = _bytes_de(pasta) if pasta.exists() else 0
        total_anexos += tamanho_anexos
        quando = _quando(meta)
        if quando is None:
            continue
        if quando < corte_sinal:
            # passou até a janela do sinal: o run inteiro sai, anexos junto
            runs_a_remover.append({
                "id": meta.get("id"), "path": ws.relpath(caminho),
                "at": quando.isoformat(),
                "bytes": caminho.stat().st_size + tamanho_anexos,
            })
        elif quando < corte_anexo and tamanho_anexos:
            # só o anexo passou: o sinal FICA, e é isso que mantém a série
            # respondendo depois que a captura daquele dia já foi descartada
            anexos_a_remover.append({
                "id": meta.get("id"), "path": ws.relpath(pasta),
                "at": quando.isoformat(), "bytes": tamanho_anexos,
                "files": len(list(pasta.rglob("*"))),
            })

    return {
        "retention": conf,
        "usage": {
            "runs": len(_runs(ws)),
            "documents_bytes": total_docs,
            "attachments_bytes": total_anexos,
            "total_bytes": total_docs + total_anexos,
        },
        "would_remove": {
            "attachments": anexos_a_remover,
            "runs": runs_a_remover,
            "bytes": sum(a["bytes"] for a in anexos_a_remover)
            + sum(r["bytes"] for r in runs_a_remover),
        },
    }


def aplicar(ws, conn) -> dict[str, Any]:
    """Executa exatamente o que a prévia prometeu, para a lixeira.

    Recalcula a prévia aqui em vez de receber a lista de quem chamou: lista
    vinda de fora envelhece entre a tela e o clique, e apagar pelo que o
    cliente mandou é como se apaga o que não devia.
    """
    plano = previa(ws)
    from .indexer import reindex_file

    removidos = {"attachments": [], "runs": [], "bytes": 0}
    for item in plano["would_remove"]["attachments"]:
        pasta = ws.root / item["path"]
        if pasta.exists():
            ws.trash(pasta)
            removidos["attachments"].append(item["id"])
            removidos["bytes"] += item["bytes"]
            # o documento perde a lista de anexos: manter o que não existe
            # mais faria a tela oferecer um print que responde 404
            _esquecer_anexos(ws, conn, item["id"])
    for item in plano["would_remove"]["runs"]:
        caminho = ws.root / item["path"]
        pasta = caminho.parent / caminho.stem
        if pasta.exists():
            ws.trash(pasta)
        if caminho.exists():
            ws.trash(caminho)
            reindex_file(ws, conn, caminho)
        removidos["runs"].append(item["id"])
        removidos["bytes"] += item["bytes"]
    return {"removed": removidos, "retention": plano["retention"]}


def _esquecer_anexos(ws, conn, run_id: str | None) -> None:
    if not run_id:
        return
    linha = conn.execute(
        "SELECT path FROM ci_runs WHERE id = ?", (run_id,)
    ).fetchone()
    if not linha:
        return
    caminho = ws.root / linha["path"]
    if not caminho.exists():
        return
    doc = frontmatter.loads(caminho.read_text(encoding="utf-8"))
    doc.metadata["attachments"] = []
    doc.metadata["attachments_expired_at"] = datetime.now(timezone.utc).isoformat()
    caminho.write_text(frontmatter.dumps(doc) + "\n", encoding="utf-8")
    from .indexer import reindex_file

    reindex_file(ws, conn, caminho)


# ---------------------------------------------------------------------------
# Limpar tudo (change 0192)


def previa_total(ws) -> dict[str, Any]:
    """O que um "limpar tudo" levaria — contado ANTES de qualquer confirmação.

    Uma confirmação que não diz o tamanho do estrago não é confirmação, é um
    obstáculo: quem clica em "sim" sem saber que são 45 execuções e 300 MB
    não decidiu nada.
    """
    runs = _runs(ws)
    anexos = 0
    for caminho, doc in runs:
        pasta = caminho.parent / caminho.stem
        if pasta.exists():
            anexos += len([p for p in pasta.rglob("*") if p.is_file()])
    base = ws.root / "ci"
    return {
        "runs": len(runs),
        "attachments": anexos,
        "bytes": _bytes_de(base) if base.exists() else 0,
        "oldest": min((_iso_de(d) for _, d in runs if _iso_de(d)), default=None),
        "newest": max((_iso_de(d) for _, d in runs if _iso_de(d)), default=None),
    }


def _iso_de(doc: dict[str, Any]) -> str | None:
    quando = _quando(doc)
    return quando.isoformat() if quando else None


def limpar_tudo(ws, conn) -> dict[str, Any]:
    """Manda a observabilidade inteira para a lixeira — não para o `rm`.

    "Limpar tudo" é a operação em que o produto mais precisa ser confiável:
    quem a usa costuma estar irritado com um dado errado, e é exatamente aí
    que se apaga o que não devia. Por isso vai para `.arbites/trash/`, como
    todo o resto, e volta enquanto a lixeira não for esvaziada.

    A cobertura vai junto, e tem de ir: mantê-la afirmaria que o período já
    foi varrido quando não há mais nada dele no disco, e a próxima busca não
    traria nada de volta (change 0190).
    """
    from . import ci_cobertura
    from .indexer import reindex_file

    plano = previa_total(ws)
    for caminho, _ in _runs(ws):
        pasta = caminho.parent / caminho.stem
        if pasta.exists():
            ws.trash(pasta)
        if caminho.exists():
            ws.trash(caminho)
            reindex_file(ws, conn, caminho)
    ci_cobertura.esquecer(ws)
    return {"removed": plano}
