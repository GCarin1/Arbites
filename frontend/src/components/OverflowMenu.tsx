import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Menu de ações (change 0131).
 *
 * Serve para tirar a ação destrutiva de perto da ação principal sem
 * escondê-la: numa tela que se abre para ler, o que apaga o trabalho não
 * deveria estar a um erro de mira do que se usa todo dia.
 *
 * Fecha no Esc, no clique fora e ao escolher — os três, pelo mesmo motivo
 * da gaveta de navegação: o gesto de sair varia de pessoa para pessoa.
 */
export function OverflowMenu({
  label = "Mais ações",
  children,
}: {
  label?: string;
  children: (fechar: () => void) => ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const gatilho = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (!box.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        gatilho.current?.focus(); // devolve o foco a quem abriu
      }
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="overflow-menu" ref={box}>
      <button
        ref={gatilho}
        className="overflow-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label}
        title={label}
      >
        <span aria-hidden="true">⋯</span>
      </button>
      {open && (
        <div className="overflow-dropdown" role="menu">
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  );
}
