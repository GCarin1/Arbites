"""Validade e recusa da credencial do provedor (change 0157).

## Por que isto existe

A pesquisa sobre o PAT devolveu um achado que muda o desenho: **não há data
de descontinuação anunciada** para o token classic — o GitHub apenas
*recomenda* o fine-grained. Mas o risco real nunca foi "o PAT vai acabar":

- o fine-grained expira em **no máximo 366 dias** (o classic pode não expirar);
- o dono da organização pode exigir aprovação e **revogar quando quiser**.

Ou seja, a credencial **vai** falhar um dia, por desenho. E com a ingestão
contínua da change 0153 ela pararia **em silêncio** — alguém descobriria
semanas depois, ao notar que a observabilidade congelou. Pior: num painel,
ausência de dado se parece com boa notícia.

## As duas decisões

**1. O estado mora fora do índice.** Um reindex reconstrói o índice do zero
(ADR 0001); se a memória da recusa morasse lá, ela sumiria no próximo reindex
e o problema voltaria a ser invisível. Fica num JSON ao lado do `auth.db`, que
é durável pelo mesmo motivo (ADR 0011).

**2. "Parado por credencial" NÃO é "não há run novo".** Os dois estados
parecem iguais na tela — nenhum dado novo — e pedem ações opostas: um exige
repor o token, o outro exige não fazer nada. Confundi-los é o defeito.

A validade em si não é segredo (o token é, e continua só no keyring — ADR
0008): é uma data, e serve justamente para ser mostrada antes de passar.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ARQUIVO = "ci_credential.json"
# Duas semanas: tempo de sobra para alguém pedir a renovação ao dono da
# organização, que costuma ser outra pessoa e costuma demorar.
AVISO_DIAS = 14


def _hoje() -> date:
    return datetime.now(timezone.utc).date()


class CredentialState:
    def __init__(self, ws) -> None:
        self.caminho = Path(ws.arbites_dir) / ARQUIVO

    # -- persistência ------------------------------------------------------

    def _ler(self) -> dict[str, Any]:
        if not self.caminho.exists():
            return {}
        try:
            return json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}  # estado corrompido não pode derrubar a instância

    def _gravar(self, dados: dict[str, Any]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps(dados, indent=2), encoding="utf-8")

    # -- eventos -----------------------------------------------------------

    def registrar_token(self, expires_at: str | None) -> None:
        """Token novo: a validade é informada por quem o criou (o provedor não
        conta ao cliente quando o token expira) e a recusa anterior morre —
        senão o problema ficaria na tela depois de resolvido."""
        dados = self._ler()
        dados["expires_at"] = expires_at or None
        dados.pop("last_refusal", None)
        dados["set_at"] = datetime.now(timezone.utc).isoformat()
        self._gravar(dados)

    def registrar_recusa(self, status: int, mensagem: str) -> None:
        dados = self._ler()
        dados["last_refusal"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "message": mensagem[:300],
        }
        self._gravar(dados)

    def registrar_sucesso(self) -> None:
        """Uma chamada que passou prova que a credencial vale agora — e
        apagar a recusa aqui é o que impede um 403 antigo de virar um
        problema eterno na tela."""
        dados = self._ler()
        if "last_refusal" not in dados and dados.get("last_success_at"):
            return  # nada mudou; não reescreve o arquivo a cada requisição
        dados.pop("last_refusal", None)
        dados["last_success_at"] = datetime.now(timezone.utc).isoformat()
        self._gravar(dados)

    # -- leitura -----------------------------------------------------------

    def status(self, configurada: bool) -> dict[str, Any]:
        dados = self._ler()
        expira = dados.get("expires_at")
        dias = None
        if expira:
            try:
                dias = (date.fromisoformat(str(expira)[:10]) - _hoje()).days
            except ValueError:
                dias = None
        return {
            "configured": configurada,
            "expires_at": expira,
            "days_until_expiry": dias,
            "last_refusal": dados.get("last_refusal"),
            "last_success_at": dados.get("last_success_at"),
            "healthy": configurada and not dados.get("last_refusal")
            and (dias is None or dias > 0),
        }

    def problemas(self, configurada: bool) -> list[dict[str, str]]:
        """Os problemas da credencial, DERIVADOS a cada leitura.

        Derivados e não gravados na tabela de avisos porque aquela tabela é
        do índice, e um reindex a esvazia: o problema voltaria a ser
        invisível exatamente no cenário que esta change existe para cobrir.
        """
        estado = self.status(configurada)
        saida: list[dict[str, str]] = []
        origem = "Credencial do GitHub"

        recusa = estado["last_refusal"]
        if recusa:
            quando = str(recusa.get("at", ""))[:10]
            saida.append({
                "source_path": origem,
                "code": "ci_credential_refused",
                "message": (
                    f"o provedor recusou a credencial em {quando}"
                    f" (HTTP {recusa.get('status')}): {recusa.get('message')}."
                    " A ingestão está PARADA por isso — não é ausência de"
                    " execução nova. Reponha o token em Administração para"
                    " retomar; o intervalo perdido volta inteiro."
                ),
                "created_at": str(recusa.get("at", "")),
            })

        def dia_ou_dias(n: int) -> str:
            return "dia" if abs(n) == 1 else "dias"

        dias = estado["days_until_expiry"]
        if configurada and dias is not None and dias <= AVISO_DIAS:
            if dias < 0:
                texto = (
                    f"a credencial expirou há {abs(dias)} {dia_ou_dias(dias)}"
                    f" ({estado['expires_at']}). Renove antes que a série"
                    " temporal ganhe um buraco."
                )
            elif dias == 0:
                texto = "a credencial expira HOJE. Renove antes do próximo run."
            else:
                texto = (
                    f"a credencial expira em {dias} {dia_ou_dias(dias)}"
                    f" ({estado['expires_at']}). Renovar leva tempo quando"
                    " depende do dono da organização — peça agora."
                )
            saida.append({
                "source_path": origem,
                "code": "ci_credential_expiring",
                "message": texto,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        return saida
