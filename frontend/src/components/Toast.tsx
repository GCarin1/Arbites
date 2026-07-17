import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";

type ToastKind = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  kind: ToastKind;
}

interface ToastApi {
  /** Confirmação transitória — o feedback de "salvo/feito" canônico. */
  toast: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

/**
 * Feedback de estado transitório (design-system 0061): confirma toda ação
 * bem-sucedida ("Salvo", "Excluído") em vez de deixar o save silencioso. Um
 * provider único no topo da app; qualquer tela chama `useToast().toast(...)`.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const seq = useRef(0);

  const toast = useCallback((message: string, kind: ToastKind = "success") => {
    const id = ++seq.current;
    setItems((old) => [...old, { id, message, kind }]);
    // auto-dismiss; erros ficam um pouco mais (o usuário precisa ler)
    window.setTimeout(
      () => setItems((old) => old.filter((t) => t.id !== id)),
      kind === "error" ? 5000 : 2600,
    );
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {items.map((t) => (
          <div
            key={t.id}
            className={`toast toast-${t.kind}`}
            onClick={() => setItems((old) => old.filter((x) => x.id !== t.id))}
          >
            <span className={`status-dot ${DOT[t.kind]}`} />
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const DOT: Record<ToastKind, string> = {
  success: "dot-col-passed",
  error: "dot-col-failed",
  info: "dot-col-in_progress",
};

/** Hook de acesso ao toast. Fora do provider, vira no-op (nunca quebra). */
export function useToast(): ToastApi {
  return useContext(ToastContext) ?? { toast: () => {} };
}
