import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Identicon } from "./Identicon";
import type { SessionUser } from "../types";

/**
 * Identidade da conta no canto superior direito, do jeito que o GitHub faz:
 * o avatar responde "com que conta eu estou gravando" sem exigir navegação,
 * e abre o menu com Perfil, Administração (só para `admin`) e Sair.
 */

// A foto muda numa tela (Perfil) e precisa aparecer em outra (o cabeçalho,
// que nunca desmonta). Um contador de versão compartilhado troca o `src` sem
// obrigar as duas telas a se conhecerem.
let avatarVersion = 0;
const versionListeners = new Set<() => void>();

export function bumpAvatarVersion(): void {
  avatarVersion += 1;
  for (const listener of versionListeners) listener();
}

function useAvatarVersion(): number {
  return useSyncExternalStore(
    useCallback((listener: () => void) => {
      versionListeners.add(listener);
      return () => versionListeners.delete(listener);
    }, []),
    () => avatarVersion,
  );
}

export function AccountAvatar({
  user,
  size = 28,
}: {
  user: SessionUser;
  size?: number;
}) {
  const version = useAvatarVersion();
  // Sem imagem o backend responde 404 — não é erro, é o sinal de desenhar o
  // identicon. O onError cobre isso sem uma chamada extra só para perguntar.
  const [broken, setBroken] = useState(false);
  useEffect(() => setBroken(false), [version]);

  if (broken) return <Identicon email={user.email} size={size} />;
  return (
    <img
      className="account-avatar-img"
      src={`/api/v1/profile/avatar?v=${version}`}
      width={size}
      height={size}
      alt={`Avatar de ${user.name || user.email}`}
      onError={() => setBroken(true)}
    />
  );
}

export function AccountMenu({
  user,
  onProfile,
  onAdmin,
  onLogout,
}: {
  user: SessionUser;
  onProfile: () => void;
  onAdmin: () => void;
  onLogout: () => void;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDocument(event: MouseEvent) {
      if (!box.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocument);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocument);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function choose(action: () => void) {
    setOpen(false);
    action();
  }

  return (
    <div className="account-menu" ref={box}>
      <button
        className="account-trigger"
        onClick={() => setOpen((v) => !v)}
        title={`${user.email} · ${user.role}`}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Conta"
      >
        <AccountAvatar user={user} />
      </button>
      {open && (
        <div className="account-dropdown" role="menu">
          <div className="account-head">
            <strong>{user.name || user.email}</strong>
            <span className="caption mono">{user.email}</span>
            <span className="caption">{user.role}</span>
          </div>
          <button role="menuitem" onClick={() => choose(onProfile)}>
            Perfil
          </button>
          {user.role === "admin" && (
            <button role="menuitem" onClick={() => choose(onAdmin)}>
              Administração
            </button>
          )}
          <button role="menuitem" onClick={() => choose(onLogout)}>
            Sair
          </button>
        </div>
      )}
    </div>
  );
}
