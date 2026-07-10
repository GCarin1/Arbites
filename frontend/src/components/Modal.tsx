import { useEffect, useRef, type ReactNode } from "react";

// Pilha de modais abertos (ex.: "Criar defeito" dentro do modal de resultado).
// Cada instância tem listener de Esc próprio no document; sem essa pilha, Esc
// fecharia TODOS os modais abertos de uma vez em vez de só o de cima.
let modalIdSeq = 0;
const openModalIds: number[] = [];

/**
 * Modal em tela com o design system da aplicação — substitui os
 * window.prompt/window.confirm nativos do browser. Fecha com Esc ou clique
 * no backdrop; trava o scroll do body e devolve o foco ao fechar.
 */
export function Modal({
  title,
  onClose,
  children,
  footer,
  initialFocus,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  // Opcional: sem footer, o único fechar é o X do header (evita botão duplicado).
  footer?: ReactNode;
  initialFocus?: React.RefObject<HTMLElement>;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const modalId = useRef(++modalIdSeq).current;
  // onClose lido por ref: não pode entrar nas deps do efeito de foco, senão
  // uma nova identidade de onClose (ex.: re-render do pai) re-dispara o foco
  // e rouba o cursor do campo em que o usuário está digitando.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    openModalIds.push(modalId);
    return () => {
      const i = openModalIds.indexOf(modalId);
      if (i !== -1) openModalIds.splice(i, 1);
    };
  }, [modalId]);

  // Foco inicial + scroll-lock: SÓ no mount (deps vazias). O initialFocus é
  // capturado uma vez de propósito.
  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";

    const target =
      initialFocus?.current ??
      panelRef.current?.querySelector<HTMLElement>("input, select, textarea, button");
    target?.focus();

    return () => {
      document.body.style.overflow = overflow;
      previouslyFocused?.focus();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Esc fecha só o modal do topo da pilha — usa a ref para sempre ver o
  // onClose atual sem re-focar.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && openModalIds[openModalIds.length - 1] === modalId) {
        e.stopPropagation();
        onCloseRef.current();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={panelRef}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

/** Diálogo de confirmação (substitui window.confirm). */
export function ConfirmModal({
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  danger = false,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      footer={
        <>
          <button onClick={onCancel}>{cancelLabel}</button>
          <button className={danger ? "danger" : "primary"} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="modal-text">{message}</p>
    </Modal>
  );
}
