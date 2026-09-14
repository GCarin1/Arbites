"""Listas de To Do (change 0164).

## A divisão de trabalho entre afazer e lista

As duas referências são diferentes de propósito, e a diferença é o desenho:

- **Afazer** é a nota adesiva: uma coisa a fazer, com prazo, status e cor.
  Nasce solta, num impulso, e é sobre ela que o sino cobra prazo.
- **Lista de To Do** é o roteiro: um conjunto de passos que só faz sentido
  junto, com um prazo da LISTA. A linha não tem prazo próprio.

E é justamente isso que dá sentido ao vínculo: quando uma linha precisa de
prazo, de status e de aparecer no sino, ela se liga a um afazer. **O afazer
traz a data; a linha traz o passo.**

## O vínculo mora em UM lado só

A relação é um-para-um, e é gravada só na LINHA (`todo: TD-0007`). Guardar
dos dois lados criaria a chance de eles se contradizerem — e aí alguém teria
de decidir qual dos dois está certo, sem ter como. O sentido inverso (de qual
linha um afazer participa) é uma CONSULTA, não um segundo dado.

## O arquivo continua legível por gente

A lista é um documento do workspace, com as linhas no frontmatter. Abrir num
editor de texto e entender é o contrato do produto inteiro (ADR 0001).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter

from .workspace import slugify

PASTA = "todolists"
STATUS = ("active", "done", "archived")


class ListaErro(Exception):
    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _hoje() -> str:
    return date.today().isoformat()


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def proximo_item_id(meta: dict[str, Any]) -> str:
    """Id da linha: sequencial e NUNCA reaproveitado.

    O contador mora no arquivo (`next_item`), e não é deduzido das linhas que
    existem agora: deduzir faz o número RECUAR quando a última linha é
    apagada, e o id volta a ser emitido. Um afazer vinculado passaria então a
    apontar para uma linha que não é a dele — sem ninguém ser avisado, porque
    nada falha.

    O máximo entre o contador e os ids presentes cobre a lista escrita à mão
    num editor de texto, que é um caso normal aqui (ADR 0001).
    """
    maior = 0
    for item in meta.get("items") or []:
        achado = re.match(r"^i(\d+)$", str(item.get("id") or ""))
        if achado:
            maior = max(maior, int(achado.group(1)))
    try:
        contador = int(meta.get("next_item") or 0)
    except (TypeError, ValueError):
        contador = 0
    proximo = max(contador, maior + 1)
    meta["next_item"] = proximo + 1
    return f"i{proximo}"


def caminho_da_lista(ws, list_id: str, titulo: str) -> Path:
    destino = ws.root / PASTA
    destino.mkdir(parents=True, exist_ok=True)
    return destino / f"{list_id}-{slugify(titulo)}.md"


def normalizar_item(bruto: dict[str, Any], ordem: int) -> dict[str, Any]:
    return {
        "id": str(bruto.get("id") or f"i{ordem + 1}"),
        "text": str(bruto.get("text") or "").strip(),
        "done": bool(bruto.get("done")),
        # o vínculo com o afazer — um só, e só deste lado
        "todo": (str(bruto.get("todo")).strip() or None) if bruto.get("todo") else None,
    }


def ler(ws, rel: str) -> tuple[dict[str, Any], str]:
    caminho = ws.root / rel
    doc = frontmatter.loads(caminho.read_text(encoding="utf-8"))
    meta = dict(doc.metadata)
    meta["items"] = [
        normalizar_item(i, n) for n, i in enumerate(meta.get("items") or [])
        if isinstance(i, dict)
    ]
    return meta, doc.content


def gravar(ws, caminho: Path, meta: dict[str, Any], corpo: str) -> None:
    post = frontmatter.Post(corpo, **{k: v for k, v in meta.items() if v is not None})
    caminho.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def criar(ws, titulo: str, due: str | None, corpo: str = "",
          itens: list[dict] | None = None) -> tuple[Path, dict[str, Any]]:
    titulo = (titulo or "").strip()
    if not titulo:
        raise ListaErro("missing_title", "a lista precisa de um título")
    list_id = ws.next_id("todolist")
    meta: dict[str, Any] = {
        "id": list_id,
        "title": titulo,
        "status": "active",
        "due": due or None,
        "created": _hoje(),
        "updated": _hoje(),
        "items": [normalizar_item(i, n) for n, i in enumerate(itens or [])],
        "next_item": len(itens or []) + 1,
    }
    caminho = caminho_da_lista(ws, list_id, titulo)
    gravar(ws, caminho, meta, corpo)
    return caminho, meta


def progresso(itens: list[dict[str, Any]]) -> dict[str, int]:
    feitos = sum(1 for i in itens if i.get("done"))
    return {"total": len(itens), "done": feitos, "open": len(itens) - feitos}


def validar_vinculo(conn, todo_id: str | None, list_id: str,
                    item_id: str) -> None:
    """Um afazer participa de UMA linha. Duas linhas apontando para o mesmo
    afazer tornam "este afazer está concluído?" uma pergunta sem resposta."""
    if not todo_id:
        return
    existe = conn.execute(
        "SELECT 1 FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not existe:
        raise ListaErro("todo_not_found", f"{todo_id} não é um afazer daqui", 404)
    ocupado = conn.execute(
        "SELECT list_id, item_id FROM todolist_items WHERE todo_id = ?"
        " AND NOT (list_id = ? AND item_id = ?)",
        (todo_id, list_id, item_id),
    ).fetchone()
    if ocupado:
        raise ListaErro(
            "todo_already_linked",
            f"{todo_id} já está vinculado a uma linha de {ocupado['list_id']} —"
            " um afazer participa de uma linha só, senão \"ele está concluído?\""
            " passa a depender de várias e não tem resposta.",
            409,
        )
