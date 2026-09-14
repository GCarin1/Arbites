"""Entrada CLI: `serve` (API + UI), `reindex` e `unlock`."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(prog="arbites")
    parser.add_argument(
        "command", nargs="?", default="serve",
        choices=["serve", "reindex", "unlock"],
    )
    parser.add_argument(
        "--workspace",
        default=os.environ.get("ARBITES_WORKSPACE", "workspace"),
        help="caminho do workspace (default: ./workspace ou $ARBITES_WORKSPACE)",
    )
    parser.add_argument("--port", type=int, default=8347)
    parser.add_argument(
        "--email", default="",
        help="unlock: destrava só esta conta (default: todas)",
    )
    args = parser.parse_args()

    # O `.env` do diretório atual, ANTES de qualquer coisa ler o ambiente
    # (change 0165). Fora do container ninguém fazia isso — quem lê o arquivo
    # no Docker é o Compose, não o Arbites — e a instância subia sem admin.
    from .envfile import carregar

    aplicadas = carregar()
    if aplicadas:
        # As CHAVES, nunca os valores: este arquivo costuma ter senha dentro.
        print(f".env aplicado: {', '.join(sorted(aplicadas))}")

    if args.command == "unlock":
        # Sair do bloqueio por tentativas sem esperar (change 0165). Quem tem
        # o arquivo na mão já é dono da instância: sem esta saída, um erro de
        # senha na própria máquina viraria quinze minutos de espera sem
        # nenhuma explicação de como encurtar.
        from . import auth as auth_ops
        from .workspace import Workspace

        ws = Workspace(args.workspace)
        ws.ensure()
        conn = auth_ops.connect_auth(ws)
        apagadas = auth_ops.clear_attempts(conn, args.email)
        alvo = args.email or "todas as contas"
        print(f"{apagadas} tentativa(s) de login descartada(s) para {alvo}.")
        contas = auth_ops.list_users(conn)
        if not contas:
            print(
                "Nenhuma conta existe neste workspace. Defina ARBITES_ADMIN_EMAIL"
                " e ARBITES_ADMIN_PASSWORD (no .env ou no ambiente) e suba de"
                " novo: o primeiro admin nasce no arranque."
            )
        return

    if args.command == "reindex":
        from .indexer import connect, reindex_full
        from .workspace import Workspace

        ws = Workspace(args.workspace)
        ws.ensure()
        stats = reindex_full(ws, connect(ws))
        print(stats)
        return

    import uvicorn

    os.environ["ARBITES_WORKSPACE"] = args.workspace
    from .api import create_app

    uvicorn.run(create_app(args.workspace), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
