"""Entrada CLI: `serve` (API + UI), `reindex` e `unlock`."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(prog="arbites")
    parser.add_argument(
        "command", nargs="?", default="serve",
        choices=["serve", "reindex", "unlock", "admin"],
    )
    parser.add_argument(
        "--workspace",
        default=os.environ.get("ARBITES_WORKSPACE", "workspace"),
        help="caminho do workspace (default: ./workspace ou $ARBITES_WORKSPACE)",
    )
    parser.add_argument("--port", type=int, default=8347)
    parser.add_argument(
        "--email", default="",
        help="unlock: destrava só esta conta (default: todas)."
             " admin: a conta a criar ou redefinir",
    )
    parser.add_argument(
        "--password", default="",
        help="admin: define a senha desta conta (12 caracteres ou mais)",
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

    if args.command == "admin":
        # "Por que 401?" tem TRÊS respostas possíveis — conta inexistente,
        # senha errada e conta não-ativa — e a API não distingue nenhuma
        # delas de fora, de propósito (evitar enumeração de contas). De
        # dentro da máquina isso vira um mistério sem saída: este comando
        # responde a pergunta e conserta (change 0166).
        from . import auth as auth_ops
        from .workspace import Workspace

        ws = Workspace(args.workspace)
        ws.ensure()
        conn = auth_ops.connect_auth(ws)

        if args.email and args.password:
            try:
                auth_ops.validate_password(args.password)
            except auth_ops.AuthError as e:
                print(f"senha recusada: {e.message}")
                raise SystemExit(2) from e
            existente = auth_ops.get_user_by_email(conn, args.email)
            if existente is None:
                auth_ops.create_user(
                    conn, args.email, args.password, name="Administrador",
                    role="admin", status="active", must_change_password=True,
                )
                print(f"conta admin CRIADA para {args.email}.")
            else:
                auth_ops.set_password(conn, existente["id"], args.password,
                                      must_change=True)
                conn.execute(
                    "UPDATE users SET role = 'admin', status = 'active'"
                    " WHERE id = ?", (existente["id"],))
                conn.commit()
                print(
                    f"conta {args.email} teve a SENHA REDEFINIDA e voltou a"
                    f" admin/ativa (estava: {existente['role']}/"
                    f"{existente['status']})."
                )
            # A senha passou pelo histórico do shell — vale para entrar uma
            # vez, não para ficar. É a mesma regra do bootstrap por ambiente.
            print("Troque a senha no primeiro login: ela ficou no histórico"
                  " do shell.")
            auth_ops.clear_attempts(conn, args.email)
            return

        if args.email or args.password:
            print("informe --email E --password juntos para criar ou redefinir.")
            raise SystemExit(2)

        contas = auth_ops.list_users(conn)
        if not contas:
            print(
                "NENHUMA conta existe neste workspace — e por isso todo login"
                " responde 401.\n"
                "Crie a primeira assim:\n"
                f"  python -m arbites admin --workspace {args.workspace}"
                " --email voce@exemplo.com --password uma-senha-de-12-ou-mais"
            )
            return
        print(f"{len(contas)} conta(s) em {ws.root}:")
        for c in contas:
            troca = " (troca obrigatória)" if c.get("must_change_password") else ""
            print(f"  {c['email']:<34} {c['role']:<8} {c['status']}{troca}")
        ativos = [c for c in contas if c["role"] == "admin"
                  and c["status"] == "active"]
        if not ativos:
            print(
                "\nNenhum admin ATIVO: uma conta pendente ou desativada"
                " responde 401 igual a senha errada, de propósito."
            )
        print(
            "\nSenha esquecida? Redefina:\n"
            f"  python -m arbites admin --workspace {args.workspace}"
            " --email <o e-mail acima> --password <nova-senha>"
        )
        return

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
