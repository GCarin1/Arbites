import { useState } from "react";
import { api } from "../api";
import type { SessionUser } from "../types";

type Mode = "login" | "register" | "password";

/** Erro da API com o código estável que o backend devolve. */
function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : "falha inesperada";
}

export function Login({
  onAuthenticated,
  signupEnabled,
  forcePasswordChange,
}: {
  onAuthenticated: (user: SessionUser) => void;
  signupEnabled: boolean;
  forcePasswordChange?: boolean;
}) {
  const [mode, setMode] = useState<Mode>(
    forcePasswordChange ? "password" : "login",
  );
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      if (mode === "login") {
        const { user } = await api.login(email, password);
        onAuthenticated(user);
      } else if (mode === "register") {
        await api.register(email, password, name);
        setMode("login");
        setPassword("");
        setNotice(
          "Cadastro recebido. Um administrador precisa liberar o acesso " +
            "antes do primeiro login.",
        );
      } else {
        if (newPassword !== confirmation) {
          setError("a confirmação não confere com a nova senha");
          return;
        }
        const { user } = await api.changePassword(password, newPassword);
        onAuthenticated(user);
      }
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  const titles: Record<Mode, string> = {
    login: "Entrar",
    register: "Criar conta",
    password: "Definir uma senha",
  };

  return (
    <div className="login-shell">
      <form className="card login-card" onSubmit={submit}>
        <div className="login-brand">
          <h1>Arbites</h1>
          <p className="muted">Gestão e rastreabilidade de testes</p>
        </div>

        <h2 className="login-title">{titles[mode]}</h2>

        {mode === "password" && (
          <p className="muted login-hint">
            Esta conta ainda usa a senha de instalação. Defina uma senha
            própria para continuar.
          </p>
        )}

        {mode !== "password" && (
          <div className="field wide">
            <label htmlFor="login-email">E-mail</label>
            <input
              id="login-email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        )}

        {mode === "register" && (
          <div className="field wide">
            <label htmlFor="login-name">Nome</label>
            <input
              id="login-name"
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
        )}

        <div className="field wide">
          <label htmlFor="login-password">
            {mode === "password" ? "Senha atual" : "Senha"}
          </label>
          <input
            id="login-password"
            type="password"
            autoComplete={
              mode === "register" ? "new-password" : "current-password"
            }
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {mode === "register" && (
            <span className="muted login-hint">Mínimo de 12 caracteres.</span>
          )}
        </div>

        {mode === "password" && (
          <>
            <div className="field wide">
              <label htmlFor="login-new">Nova senha</label>
              <input
                id="login-new"
                type="password"
                autoComplete="new-password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <span className="muted login-hint">Mínimo de 12 caracteres.</span>
            </div>
            <div className="field wide">
              <label htmlFor="login-confirm">Confirmar nova senha</label>
              <input
                id="login-confirm"
                type="password"
                autoComplete="new-password"
                required
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
              />
            </div>
          </>
        )}

        {error && (
          <p className="login-error" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="login-notice" role="status">
            {notice}
          </p>
        )}

        <button className="primary login-submit" type="submit" disabled={busy}>
          {busy ? "Aguarde…" : titles[mode]}
        </button>

        {mode !== "password" && signupEnabled && (
          <button
            type="button"
            className="login-switch"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
              setNotice("");
            }}
          >
            {mode === "login"
              ? "Não tem conta? Cadastre-se"
              : "Já tem conta? Entrar"}
          </button>
        )}
      </form>
    </div>
  );
}
