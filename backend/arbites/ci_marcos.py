"""Marcos: o ponto fixo contra o qual se mede melhora (change 0199).

## Por que um marco, e não "o período anterior"

O painel já compara contra os 30 dias anteriores, e essa janela **desliza**.
Se a suíte piora devagar todo mês, cada comparação isolada parece estável e o
ano inteiro foi ladeira abaixo sem nenhum alerta. A média móvel é cega para a
degradação lenta, que é justamente a que mais custa caro.

Um marco é um ponto FIXO com nome: "v2.14 em cer", "depois do mutirão de
acessibilidade", "início do trimestre". Tudo passa a ser medido contra ele até
alguém escolher outro — e a pergunta "melhoramos?" ganha uma resposta que não
se desfaz sozinha com o tempo.

## Por que arquivo, e não linha no índice

Um marco é trabalho de quem opera: alguém decidiu que aquele instante importa
e deu um nome a ele. Perder isso num reindex seria perder decisão, não cache
(ADR 0001). Mora em `ci/marcos/`, como as análises.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import frontmatter

PASTA = "ci/marcos"
PREFIXO = "MRC"


class MarcoError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def proximo_id(ws) -> str:
    """`MRC-YYYYMMDD-N`: ordenável, legível e único no dia."""
    hoje = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = ws.root / PASTA
    usados = ({p.stem for p in base.glob(f"{PREFIXO}-{hoje}-*.md")}
              if base.exists() else set())
    n = 1
    while f"{PREFIXO}-{hoje}-{n}" in usados:
        n += 1
    return f"{PREFIXO}-{hoje}-{n}"


def caminho(marco_id: str) -> str:
    return f"{PASTA}/{marco_id}.md"


def _validar_id(marco_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", marco_id or ""):
        raise MarcoError("invalid_id", "identificador inválido", 422)
    return marco_id


def _instante(bruto: Any) -> str:
    """Aceita data ou data-hora, e devolve sempre o instante completo em UTC.

    Quem marca "a v2.14 subiu em 12 de setembro" digita a data; comparar
    contra `2026-09-12` sem hora compararia contra a meia-noite e deixaria o
    próprio dia do marco do lado errado da conta.
    """
    texto = str(bruto or "").strip()
    if not texto:
        return _agora()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        texto += "T00:00:00+00:00"
    try:
        quando = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError as e:
        raise MarcoError("invalid_date",
                         f"data inválida: {bruto!r}", 422) from e
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    return quando.astimezone(timezone.utc).isoformat()


def criar(ws, nome: str, quando: Any = None, nota: str = "",
          repo: str | None = None) -> dict[str, Any]:
    nome = str(nome or "").strip()
    if not nome:
        raise MarcoError("no_name", "o marco precisa de um nome — é ele que"
                         " diz o que aconteceu naquele instante", 422)
    marco_id = proximo_id(ws)
    meta = {
        "id": marco_id,
        "kind": "ci_milestone",
        "name": nome[:120],
        "at": _instante(quando),
        "created_at": _agora(),
        # Um marco pode valer só para um repositório: a subida do trader não
        # é um marco para a suíte de back.
        "repo": (repo or "").strip() or None,
    }
    destino = ws.root / caminho(marco_id)
    destino.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(str(nota or "").strip(),
                            **{k: v for k, v in meta.items() if v is not None})
    destino.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return {**meta, "note": str(nota or "").strip(), "path": caminho(marco_id)}


def listar(ws, limite: int = 100) -> list[dict[str, Any]]:
    """Do mais recente para o mais antigo — pelo INSTANTE marcado, não pela
    data de criação: alguém pode registrar hoje um marco de semana passada."""
    base = ws.root / PASTA
    if not base.exists():
        return []
    saida = []
    for arquivo in base.glob(f"{PREFIXO}-*.md"):
        try:
            post = frontmatter.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        saida.append({
            "id": arquivo.stem,
            "name": post.metadata.get("name") or arquivo.stem,
            "at": post.metadata.get("at"),
            "repo": post.metadata.get("repo"),
            "note": post.content.strip(),
            "path": caminho(arquivo.stem),
        })
    saida.sort(key=lambda m: str(m.get("at") or ""), reverse=True)
    return saida[:limite]


def ler(ws, marco_id: str) -> dict[str, Any]:
    _validar_id(marco_id)
    arquivo = ws.root / caminho(marco_id)
    if not arquivo.is_file():
        raise MarcoError("not_found", f"marco {marco_id} não existe", 404)
    post = frontmatter.loads(arquivo.read_text(encoding="utf-8"))
    return {
        "id": marco_id,
        "name": post.metadata.get("name") or marco_id,
        "at": post.metadata.get("at"),
        "repo": post.metadata.get("repo"),
        "note": post.content.strip(),
        "path": caminho(marco_id),
    }


def remover(ws, marco_id: str) -> dict[str, Any]:
    """Para a lixeira, como todo o resto do Arbites."""
    marco = ler(ws, marco_id)
    ws.trash(ws.root / caminho(marco_id))
    return marco
