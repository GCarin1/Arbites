import { useCallback, useEffect, useState } from "react";
import { api, onPasswordChangeRequired, onUnauthenticated } from "../api";
import type { SessionUser } from "../types";
import { Login } from "./Login";

type State =
  | { phase: "checking" }
  | {
      phase: "anonymous";
      signupEnabled: boolean;
      noAdmin?: boolean;
      ownerDeclared?: boolean;
    }
  | { phase: "must-change"; user: SessionUser }
  | { phase: "authenticated"; user: SessionUser };

/**
 * Porteiro da SPA: resolve a sessão antes de montar a aplicação e devolve o
 * usuário à tela de login quando o backend responde 401 no meio do uso
 * (sessão expirada, conta desativada, papel trocado).
 */
export function AuthGate({
  children,
}: {
  children: (user: SessionUser, logout: () => void) => React.ReactNode;
}) {
  const [state, setState] = useState<State>({ phase: "checking" });

  const check = useCallback(async () => {
    try {
      const me = await api.me();
      if (!me.auth_enabled && me.user) {
        setState({ phase: "authenticated", user: me.user });
        return;
      }
      if (!me.user) {
        setState({
          phase: "anonymous",
          signupEnabled: me.signup_enabled !== false,
          noAdmin: me.no_admin === true,
          ownerDeclared: me.owner_declared === true,
        });
        return;
      }
      setState(
        me.user.must_change_password
          ? { phase: "must-change", user: me.user }
          : { phase: "authenticated", user: me.user },
      );
    } catch {
      setState({ phase: "anonymous", signupEnabled: false });
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  useEffect(() => {
    // Qualquer 401 vindo de qualquer chamada devolve para o login, sem
    // esperar o usuário topar num erro solto de tela.
    return onUnauthenticated(() => {
      setState({ phase: "anonymous", signupEnabled: true });
    });
  }, []);

  useEffect(() => {
    // E qualquer 403 `password_change_required` devolve para a troca — a
    // obrigação pode nascer com o app já montado (um admin redefine a senha
    // pelo painel, ou pelo comando local), e aí a sessão segue viva
    // respondendo 403 em tudo.
    return onPasswordChangeRequired(() => {
      setState((atual) =>
        atual.phase === "authenticated"
          ? { phase: "must-change", user: atual.user }
          : atual,
      );
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setState({ phase: "anonymous", signupEnabled: true });
    }
  }, []);

  if (state.phase === "checking") {
    return <div className="login-shell muted">Verificando sessão…</div>;
  }

  if (state.phase === "anonymous") {
    return (
      <Login
        key="anonymous"
        signupEnabled={state.signupEnabled}
        noAdmin={state.noAdmin === true}
        ownerDeclared={state.ownerDeclared === true}
        onAuthenticated={(user) =>
          setState(
            user.must_change_password
              ? { phase: "must-change", user }
              : { phase: "authenticated", user },
          )
        }
      />
    );
  }

  if (state.phase === "must-change") {
    return (
      // A `key` e o que importa aqui: sem ela o React reaproveita a mesma
      // instancia de <Login> da fase anonima, e o `useState` inicial que
      // escolhe o modo "password" NAO roda de novo — a tela continuava
      // mostrando "Entrar" como se o login nao tivesse acontecido
      // (change 0169).
      <Login
        key="must-change"
        forcePasswordChange
        signupEnabled={false}
        onAuthenticated={(user) =>
          // Nunca dar a fase "authenticated" por decreto: quem ainda deve a
          // troca volta para ca, em vez de montar o app inteiro e levar 403
          // em cada chamada sem saida.
          setState(
            user.must_change_password
              ? { phase: "must-change", user }
              : { phase: "authenticated", user },
          )
        }
      />
    );
  }

  return <>{children(state.user, logout)}</>;
}
