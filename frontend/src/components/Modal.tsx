import { useEffect, useRef, useState, type ReactNode } from "react";

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
  dirty = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  // Opcional: sem footer, o único fechar é o X do header (evita botão duplicado).
  footer?: ReactNode;
  initialFocus?: React.RefObject<HTMLElement>;
  // Quando true, fechar sem salvar (Esc/backdrop/X) pede confirmação —
  // evita perder o que foi digitado em silêncio (design-system 0061).
  dirty?: boolean;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const modalId = useRef(++modalIdSeq).current;
  const [confirmingClose, setConfirmingClose] = useState(false);

  // Toda tentativa de fechar passa por aqui: se há alteração pendente, pede
  // confirmação em vez de descartar direto.
  const requestClose = () => {
    if (dirtyRef.current) setConfirmingClose(true);
    else onClose();
  };
  // lido por ref pelos listeners (Esc) que montam uma vez só
  const requestCloseRef = useRef(requestClose);
  requestCloseRef.current = requestClose;
  const dirtyRef = useRef(dirty);
  dirtyRef.current = dirty;

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
  // requestClose atual sem re-focar.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && openModalIds[openModalIds.length - 1] === modalId) {
        e.stopPropagation();
        requestCloseRef.current();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) requestClose();
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
          <button className="modal-close" onClick={requestClose} aria-label="Fechar">
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
      {confirmingClose && (
        <ConfirmModal
          title="Descartar alterações?"
          message="Há alterações não salvas neste formulário. Fechar mesmo assim?"
          confirmLabel="Descartar"
          danger
          onConfirm={() => {
            setConfirmingClose(false);
            onClose();
          }}
          onCancel={() => setConfirmingClose(false)}
        />
      )}
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
