"""Identidade externa e a porta para sistemas de fora (change 0145, ADR 0015).

O Arbites não é a ferramenta oficial de gestão de teste da empresa, e não
tenta ser. Este módulo é a ponte: ele guarda TRÊS coisas e nada mais.

1. **O vínculo** — o que daqui corresponde a que lá, em qual sistema, em que
   revisão, e com que conteúdo na última sincronia.
2. **A porta** — o que cada ferramenta externa consegue representar, com
   CAPACIDADES declaradas em vez de denominador comum.
3. **O conflito** — quando os dois lados mudaram, quem decide é uma pessoa.

O que ele NÃO faz é transportar. Nos fluxos com humano no meio quem atravessa
as pontas é o agente, via MCP.

## Por que o vínculo mora no arquivo

O índice é descartável (ADR 0001): um reindex o reconstrói do zero. Se o
vínculo morasse só lá, um reindex apagaria a memória de tudo o que já foi
sincronizado, e a próxima sincronia recriaria no sistema oficial tudo o que
já existe. O frontmatter é a fonte, o índice é a consulta.

## Por que `synced_hash` e não só "data da última sincronia"

Data responde "quando"; ela não responde "mudou?". Com o hash do conteúdo no
momento da sincronia dá para comparar: o local mudou se o hash de agora é
diferente do guardado. Sem isso não existe detecção de conflito — só
sobrescrita, que é perda silenciosa de dado.
"""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

# -- capacidades ------------------------------------------------------------
#
# Não existe denominador comum entre um quadro Kanban e um gestor de teste: o
# Businessmap não tem caso de teste, execução nem evidência como conceito; o
# Xray tem os quatro nativos. Cada adaptador declara o que consegue
# representar, e o que não consegue é RECUSADO EM VOZ ALTA no preview — nunca
# descartado em silêncio.

ARTEFATOS = ("testcase", "execution", "result", "evidence", "folder")


class Capabilities:
    """O que uma ferramenta externa consegue representar, e sob que forma.

    `None` significa "não representa". A string diz COMO representa, porque
    "representa evidência" quer dizer coisas diferentes em ferramentas
    diferentes — anexo binário e link para um caminho não são a mesma
    promessa.
    """

    def __init__(self, system: str, label: str, **formas: str | None) -> None:
        self.system = system
        self.label = label
        self.formas = {a: formas.get(a) for a in ARTEFATOS}

    def suporta(self, artefato: str) -> bool:
        return bool(self.formas.get(artefato))

    def nao_representa(self, artefatos: Iterable[str]) -> list[str]:
        """O que desta lista a ferramenta não guarda — o texto do preview."""
        return [a for a in artefatos if not self.suporta(a)]

    def as_dict(self) -> dict[str, Any]:
        return {"system": self.system, "label": self.label, "supports": self.formas}


class ExternalTracker:
    """A porta. Um adaptador implementa isto; ninguém chama fora daqui.

    Deliberadamente pequena: buscar, criar/atualizar e ler a revisão. Tudo o
    que for específico de uma ferramenta mora no adaptador, não aqui — a
    tentação de "só mais um campo para o Businessmap" é o caminho para a
    porta virar o formato de UMA ferramenta.
    """

    capabilities: Capabilities

    async def fetch(self, remote_id: str) -> dict[str, Any] | None:  # pragma: no cover
        raise NotImplementedError

    async def upsert(self, artefato: dict[str, Any],
                     remote_id: str | None) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


# -- o vínculo --------------------------------------------------------------

CAMPO = "external"  # a chave no frontmatter


def content_hash(body: str) -> str:
    """Hash do conteúdo que a sincronia enviou.

    Só o corpo, de propósito: o frontmatter guarda o próprio vínculo, e
    incluí-lo faria toda sincronia mudar o hash que ela acabou de gravar —
    o artefato nasceria pendente de si mesmo.
    """
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()[:16]


def read_links(meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Vínculos do frontmatter, tolerante ao que veio antes.

    Aceita a forma antiga (`external_key` textual, ADR 0007) como um vínculo
    sem sistema: ele continua servindo para um humano clicar, e migra quando
    alguém o ligar de verdade.
    """
    bruto = meta.get(CAMPO)
    saida: list[dict[str, Any]] = []
    if isinstance(bruto, list):
        for item in bruto:
            if isinstance(item, dict) and item.get("system") and item.get("id"):
                saida.append({
                    "system": str(item["system"]),
                    "id": str(item["id"]),
                    "revision": item.get("revision"),
                    "synced_hash": item.get("synced_hash"),
                    "synced_at": item.get("synced_at"),
                })
    return saida


def link_for(meta: dict[str, Any], system: str) -> dict[str, Any] | None:
    for item in read_links(meta):
        if item["system"] == system:
            return item
    return None


def upsert_link(meta: dict[str, Any], system: str, remote_id: str,
                revision: str | None, synced_hash: str | None,
                synced_at: str) -> list[dict[str, Any]]:
    """Grava o vínculo de UM sistema, preservando os dos outros.

    Mais de um por artefato de propósito: uma migração corporativa tem os
    dois sistemas vivos ao mesmo tempo, e perder o vínculo antigo enquanto o
    novo nasce é perder o rastro justamente quando ele mais importa.
    """
    atuais = [item for item in read_links(meta) if item["system"] != system]
    atuais.append({
        "system": system,
        "id": remote_id,
        "revision": revision,
        "synced_hash": synced_hash,
        "synced_at": synced_at,
    })
    return sorted(atuais, key=lambda item: item["system"])


def remove_link(meta: dict[str, Any], system: str) -> list[dict[str, Any]]:
    return [item for item in read_links(meta) if item["system"] != system]


# -- pendência e conflito ---------------------------------------------------

ESTADOS = ("never_synced", "in_sync", "local_changed", "remote_changed", "conflict")


def sync_state(vinculo: dict[str, Any] | None, hash_atual: str,
               revisao_remota: str | None = None) -> str:
    """Compara os dois lados e devolve o estado — sem escolher nenhum.

    `revisao_remota` é opcional porque nem sempre se acabou de olhar o
    remoto: sem ela a pergunta respondida é só "mudou aqui?".
    """
    if vinculo is None:
        return "never_synced"
    local_mudou = bool(vinculo.get("synced_hash")) and vinculo["synced_hash"] != hash_atual
    remoto_mudou = (
        revisao_remota is not None
        and vinculo.get("revision") is not None
        and str(revisao_remota) != str(vinculo["revision"])
    )
    if local_mudou and remoto_mudou:
        # NUNCA decidido aqui: vai para a tela Problemas, onde uma pessoa
        # escolhe com o diff dos dois lados na frente (ADR 0015).
        return "conflict"
    if local_mudou:
        return "local_changed"
    if remoto_mudou:
        return "remote_changed"
    return "in_sync"


# -- adaptadores conhecidos -------------------------------------------------
#
# Só as CAPACIDADES por enquanto: o transporte de cada um chega nas changes
# 0148 (arquivo) e 0150 (volume). Declará-las agora não é adiantar trabalho —
# é o que permite ao preview dizer o que ficará de fora ANTES de alguém
# sincronizar e descobrir depois.

ADAPTADORES: dict[str, Capabilities] = {
    "businessmap": Capabilities(
        "businessmap", "Businessmap (Kanbanize)",
        # é um quadro Kanban: não tem caso de teste nem execução como
        # conceito, então caso vira card e execução vira card
        testcase="card", execution="card", result="checklist",
        evidence="attachment", folder="lane",
    ),
    "xray": Capabilities(
        "xray", "Xray (Jira)",
        testcase="native", execution="native", result="native",
        evidence="native", folder="folder",
    ),
    "file": Capabilities(
        "file", "Arquivo (CSV / Cucumber JSON)",
        testcase="row", execution="row", result="row",
        # o CSV carrega o CAMINHO da evidência, não o binário — dizer isso
        # antes é a diferença entre uma escolha e uma surpresa
        evidence="path", folder="column",
    ),
}
