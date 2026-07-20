import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { ConfirmModal } from "./Modal";
import { useToast } from "./Toast";
import type { TrashItem, Warning } from "../types";

export function WarningsView({
  warnings,
  onChanged,
  onError,
}: {
  warnings: Warning[];
  onChanged?: () => void;
  onError?: (message: string) => void;
}) {
  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Problemas ({warnings.length})</h1>
      </div>
      <p className="subtitle">
        Avisos de integridade do índice e a lixeira do workspace — nada é
        apagado de vez sem você mandar.
      </p>

      {warnings.length === 0 ? (
        <div className="empty-state block">
          <div className="empty-title">Tudo consistente</div>
          <div className="empty-body">
            Nenhum problema de integridade no workspace.
          </div>
        </div>
      ) : (
        <div className="table-wrap block">
          <table className="dense">
            <thead>
              <tr>
                <th>Arquivo</th>
                <th>Código</th>
                <th>Mensagem</th>
              </tr>
            </thead>
            <tbody>
              {warnings.map((warning, i) => (
                <tr key={i}>
                  <td className="mono">{warning.source_path}</td>
                  <td className="mono">{warning.code}</td>
                  <td>{warning.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <TrashCard onChanged={onChanged} onError={onError} />
    </div>
  );
}

function fmt(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

/** Lixeira do workspace (0081) — lista, restaura e esvazia. */
function TrashCard({
  onChanged,
  onError,
}: {
  onChanged?: () => void;
  onError?: (message: string) => void;
}) {
  const [items, setItems] = useState<TrashItem[]>([]);
  const [confirmEmpty, setConfirmEmpty] = useState(false);
  const { toast } = useToast();

  const load = useCallback(() => {
    api.trash().then(setItems).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function restore(item: TrashItem) {
    try {
      await api.restoreTrash(item.name);
      toast(`Restaurado: ${item.name}`, "success");
      load();
      onChanged?.();
    } catch (e) {
      onError?.(e instanceof Error ? e.message : String(e));
    }
  }

  async function empty() {
    setConfirmEmpty(false);
    try {
      const r = await api.emptyTrash();
      toast(`Lixeira esvaziada (${r.removed} item(ns))`, "success");
      load();
    } catch (e) {
      onError?.(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="card block">
      <div className="card-head">
        <h3>Lixeira</h3>
        <span className="spacer" />
        <span className="caption muted">
          {items.length} item(ns) — tudo que foi excluído fica aqui até você esvaziar
        </span>
        {items.length > 0 && (
          <button className="btn-sm danger" onClick={() => setConfirmEmpty(true)}>
            Esvaziar
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <p className="caption muted">Lixeira vazia.</p>
      ) : (
        <div className="table-wrap">
          <table className="dense">
            <thead>
              <tr>
                <th>Item</th>
                <th>Tipo</th>
                <th>Origem</th>
                <th>Excluído em</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.name}>
                  <td className="mono">{item.name}</td>
                  <td>{item.kind}</td>
                  <td className="mono muted">{item.origin ?? "—"}</td>
                  <td className="caption muted">{fmt(item.trashed_at)}</td>
                  <td>
                    <button className="btn-sm" onClick={() => void restore(item)}>
                      Restaurar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {confirmEmpty && (
        <ConfirmModal
          title="Esvaziar lixeira"
          message={`Apagar de vez ${items.length} item(ns)? Esta ação não pode ser desfeita.`}
          confirmLabel="Esvaziar lixeira"
          danger
          onConfirm={() => void empty()}
          onCancel={() => setConfirmEmpty(false)}
        />
      )}
    </div>
  );
}
