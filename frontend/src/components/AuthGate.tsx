import { useCallback, useEffect, useState } from "react";
import { api, onUnauthenticated } from "../api";
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
      <Login
        forcePasswordChange
        signupEnabled={false}
        onAuthenticated={(user) => setState({ phase: "authenticated", user })}
      />
    );
  }

  return <>{children(state.user, logout)}</>;
}
