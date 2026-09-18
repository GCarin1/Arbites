"""Quanto melhorou desde o marco (change 0199).

## A pergunta, e por que a resposta antiga não servia

"Melhoramos?" tinha uma resposta no painel — cada número traz "vs. período
anterior". Só que essa janela DESLIZA: se a suíte piora devagar todo mês, cada
comparação isolada parece estável e o ano inteiro foi ladeira abaixo. A média
móvel é cega justamente para a degradação lenta.

Aqui a base é FIXA: um marco nomeado. "Desde que a v2.14 subiu em cer" tem a
mesma resposta hoje e daqui a três meses — e é por isso que ela serve para
prestar contas.

## As duas janelas

`antes` é a janela de MESMO TAMANHO imediatamente anterior ao marco, e `depois`
vai do marco até agora. Iguais em duração de propósito: comparar 7 dias contra
90 diria mais sobre o tamanho das amostras que sobre o produto.

## O que é "melhor"

Para taxa e cenários aprovados, mais é melhor. Para falhas, violações e
duração, menos é melhor. Para um sinal DECLARADO, o Arbites não sabe — e não
inventa: quem instala declara `direction` em `observability.goals`, e sem isso
o número aparece com a variação e sem julgamento (ADR 0016).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from . import ci_ingest, ci_marcos


def _instante(bruto: Any) -> datetime | None:
    if not bruto:
        return None
    try:
        return datetime.fromisoformat(str(bruto).replace("Z", "+00:00"))
    except ValueError:
        return None


def _variacao(antes: float | None, depois: float | None) -> float | None:
    if antes in (None, 0) or depois is None:
        return None
    return round((depois - antes) / abs(antes) * 100, 1)


def _veredito(antes: float | None, depois: float | None,
              direcao: str | None) -> str:
    """melhorou | piorou | igual | indefinido.

    `indefinido` não é falha de cálculo: é o Arbites recusando julgar um sinal
    cuja direção ninguém declarou. Chutar que "menos é melhor" acertaria na
    maioria e erraria em cobertura, disponibilidade e quantidade de testes —
    e um veredito errado é pior que nenhum.
    """
    if antes is None or depois is None:
        return "sem base"
    if direcao not in ("lower", "higher"):
        return "indefinido"
    if depois == antes:
        return "igual"
    subiu = depois > antes
    return "melhorou" if subiu == (direcao == "higher") else "piorou"


def _linha(rotulo: str, antes: float | None, depois: float | None,
           unidade: str | None, direcao: str | None,
           chave: str | None = None) -> dict[str, Any]:
    return {
        "key": chave or rotulo,
        "label": rotulo,
        "before": antes,
        "after": depois,
        "unit": unidade,
        "delta": None if (antes is None or depois is None)
        else round(depois - antes, 2),
        "delta_pct": _variacao(antes, depois),
        "direction": direcao,
        "verdict": _veredito(antes, depois, direcao),
    }


def _runs(conn, desde: str, ate: str, repo: str | None) -> list[dict]:
    sql = ("SELECT id, conclusion FROM ci_runs"
           " WHERE COALESCE(started_at, ingested_at) >= ?"
           " AND COALESCE(started_at, ingested_at) < ?")
    args: list[Any] = [desde, ate]
    if repo:
        sql += " AND (repo = ? OR trigger_repo = ?)"
        args += [repo, repo]
    return [dict(r) for r in conn.execute(sql, args)]


def _media_do_sinal(conn, nome: str, desde: str, ate: str) -> float | None:
    linha = conn.execute(
        "SELECT AVG(value) m FROM ci_signals WHERE name = ?"
        " AND at >= ? AND at < ?", (nome, desde, ate)).fetchone()
    return round(linha["m"], 2) if linha and linha["m"] is not None else None


def _violacoes(conn, desde: str, ate: str, impacto: str | None = None) -> int:
    sql = ("SELECT COALESCE(SUM(count), 0) t FROM ci_findings"
           " WHERE at >= ? AND at < ?")
    args: list[Any] = [desde, ate]
    if impacto:
        sql += " AND impact = ?"
        args.append(impacto)
    return int(conn.execute(sql, args).fetchone()["t"] or 0)


def _cenarios_que_falharam(conn, desde: str, ate: str,
                           repo: str | None) -> set[str]:
    sql = ("SELECT DISTINCT scenario FROM ci_scenarios"
           " WHERE at >= ? AND at < ? AND status IN ('failed','blocked')")
    args: list[Any] = [desde, ate]
    if repo:
        sql += (" AND run_id IN (SELECT id FROM ci_runs WHERE repo = ?"
                " OR trigger_repo = ?)")
        args += [repo, repo]
    return {r["scenario"] for r in conn.execute(sql, args)}


def _moldes(conn, desde: str, ate: str) -> dict[str, int]:
    saida: dict[str, int] = {}
    for linha in conn.execute(
        "SELECT error FROM ci_scenarios WHERE at >= ? AND at < ?"
        " AND error IS NOT NULL AND error != ''", (desde, ate)
    ):
        molde = ci_ingest.molde_do_erro(linha["error"])
        if molde:
            saida[molde] = saida.get(molde, 0) + 1
    return saida


def evolucao(ws, conn, marco_id: str, repo: str | None = None) -> dict[str, Any]:
    """O relatório inteiro, pronto para a tela e para o export."""
    marco = ci_marcos.ler(ws, marco_id)
    inicio = _instante(marco.get("at"))
    if inicio is None:
        raise ci_marcos.MarcoError("invalid_date",
                                   "o marco não tem instante válido", 422)
    agora = datetime.now(timezone.utc)
    if inicio > agora:
        raise ci_marcos.MarcoError(
            "future_milestone",
            "o marco está no futuro — não há 'depois' para medir ainda", 422)
    duracao = agora - inicio
    antes_de = (inicio - duracao).isoformat()
    marcado = inicio.isoformat()
    ate = agora.isoformat()
    # O marco pode valer só para um repositório; o filtro da tela ganha dele
    # quando nada foi escolhido.
    repo = repo or marco.get("repo")

    metas = ci_ingest._metas(ws)
    antes_runs = _runs(conn, antes_de, marcado, repo)
    depois_runs = _runs(conn, marcado, ate, repo)
    taxa_antes = ci_ingest.taxa_de_sucesso(r["conclusion"] for r in antes_runs)
    taxa_depois = ci_ingest.taxa_de_sucesso(r["conclusion"] for r in depois_runs)

    linhas = [
        _linha("Taxa de sucesso", taxa_antes[0], taxa_depois[0], "%", "higher",
               "success_rate"),
        _linha("Execuções conclusivas", float(taxa_antes[1]),
               float(taxa_depois[1]), "count", None, "conclusive_runs"),
        _linha("Violações de acessibilidade",
               float(_violacoes(conn, antes_de, marcado)),
               float(_violacoes(conn, marcado, ate)), "count", "lower",
               "a11y_total"),
        _linha("Violações críticas",
               float(_violacoes(conn, antes_de, marcado, "critical")),
               float(_violacoes(conn, marcado, ate, "critical")), "count",
               "lower", "a11y_critical"),
    ]
    # Cada sinal com série nos dois lados — declarado ou derivado.
    for sinal in ci_ingest.nomes_de_sinal(conn):
        nome = sinal["name"]
        meta = metas.get(nome) or {}
        direcao = meta.get("direction") or _DIRECAO_PADRAO.get(nome)
        linhas.append(_linha(
            nome, _media_do_sinal(conn, nome, antes_de, marcado),
            _media_do_sinal(conn, nome, marcado, ate),
            sinal.get("unit"), direcao, nome))

    falhavam = _cenarios_que_falharam(conn, antes_de, marcado, repo)
    falham = _cenarios_que_falharam(conn, marcado, ate, repo)
    moldes_antes = _moldes(conn, antes_de, marcado)
    moldes_depois = _moldes(conn, marcado, ate)

    return {
        "milestone": marco,
        "repo": repo,
        "before": {"since": antes_de, "until": marcado, "runs": len(antes_runs)},
        "after": {"since": marcado, "until": ate, "runs": len(depois_runs)},
        "days": max(round(duracao.total_seconds() / 86400, 1), 0.0),
        "metrics": linhas,
        "scenarios": {
            # O que o relatório precisa responder é MUDANÇA de estado, não
            # quantidade: "estes três pararam de falhar" é acionável de um
            # jeito que "18 falhas contra 21" nunca é.
            "resolvidos": sorted(falhavam - falham),
            "novos": sorted(falham - falhavam),
            "persistentes": sorted(falhavam & falham),
        },
        "errors": {
            "resolvidos": sorted(set(moldes_antes) - set(moldes_depois)),
            "novos": sorted(set(moldes_depois) - set(moldes_antes)),
        },
        "summary": _resumo(linhas, falhavam, falham),
    }


# Para as medidas que o próprio Arbites calcula (ADR 0019), a direção é
# conhecida — foi ele que as definiu. Para sinal DECLARADO, continua sendo
# configuração de quem instala, e sem ela não há julgamento.
_DIRECAO_PADRAO = {
    "resultado": "higher",
    "cenarios_taxa": "higher",
    "cenarios_falhos": "lower",
    "jobs_falhos": "lower",
    "duracao_min": "lower",
    "acessibilidade_violacoes": "lower",
    "acessibilidade_critical": "lower",
    "acessibilidade_serious": "lower",
    "wcag_criterios_violados": "lower",
}


def _resumo(linhas: list[dict], falhavam: set[str], falham: set[str]) -> dict:
    melhor = [l for l in linhas if l["verdict"] == "melhorou"]
    pior = [l for l in linhas if l["verdict"] == "piorou"]
    return {
        "melhorou": len(melhor),
        "piorou": len(pior),
        "sem_julgamento": len([l for l in linhas
                               if l["verdict"] == "indefinido"]),
        "cenarios_resolvidos": len(falhavam - falham),
        "cenarios_novos": len(falham - falhavam),
        "veredito": ("melhorou" if len(melhor) > len(pior)
                     else "piorou" if len(pior) > len(melhor) else "igual"),
    }
