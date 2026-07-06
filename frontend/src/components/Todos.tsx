import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import type { Todo } from "../types";

const STATUS_DOT: Record<string, string> = {
  open: "dot-col-pending",
  doing: "dot-col-in_progress",
  blocked: "dot-col-blocked",
  done: "dot-col-passed",
};
const STATUSES: Todo["status"][] = ["open", "doing", "blocked", "done"];

export function Todos({ onError }: { onError: (message: string) => void }) {
  const [items, setItems] = useState<Todo[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [editing, setEditing] = useState<Todo | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Todo | null>(null);

  const load = useCallback(() => {
    const q = statusFilter ? `?status=${statusFilter}` : "";
    api
      .todos(q)
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [statusFilter, onError]);

  useEffect(() => {
    load();
  }, [load]);

  async function quickStatus(todo: Todo, status: Todo["status"]) {
    try {
      await api.updateTodo(todo.id, { status });
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(todo: Todo) {
    setConfirmDelete(null);
    try {
      await api.deleteTodo(todo.id);
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const active = items.filter((t) => t.status !== "done");
  const done = items.filter((t) => t.status === "done");
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Afazeres</h1>
        <span className="spacer" />
        <div className="head-controls">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">Todos os status</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button className="primary" onClick={() => setEditing("new")}>
            Novo afazer
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nenhum afazer</div>
          <div className="empty-body">
            Crie afazeres com data, status e links para CTs, execuções ou stories.
            Impedimentos (blocked) entram na daily.
          </div>
        </div>
      ) : (
        <>
          {active.length > 0 && (
            <TodoTable
              rows={active}
              today={today}
              onEdit={setEditing}
              onDelete={setConfirmDelete}
              onStatus={quickStatus}
            />
          )}
          {done.length > 0 && (
            <>
              <h3 className="section-title">Concluídos ({done.length})</h3>
              <TodoTable
                rows={done}
                today={today}
                onEdit={setEditing}
                onDelete={setConfirmDelete}
                onStatus={quickStatus}
              />
            </>
          )}
        </>
      )}

      {editing && (
        <TodoModal
          todo={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
          onError={onError}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title="Excluir afazer"
          message={
            <>
              Mover <span className="mono">{confirmDelete.id}</span> para a lixeira?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove(confirmDelete)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}
    </div>
  );
}

function TodoTable({
  rows,
  today,
  onEdit,
  onDelete,
  onStatus,
}: {
  rows: Todo[];
  today: string;
  onEdit: (t: Todo) => void;
  onDelete: (t: Todo) => void;
  onStatus: (t: Todo, s: Todo["status"]) => void;
}) {
  return (
    <div className="table-wrap" style={{ marginBottom: 24 }}>
      <table className="dense">
        <thead>
          <tr>
            <th>Status</th>
            <th>Afazer</th>
            <th>Prazo</th>
            <th>Squad</th>
            <th>Links</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => {
            const overdue = t.due && t.status !== "done" && t.due < today;
            return (
              <tr key={t.id}>
                <td>
                  <select
                    className="status-select"
                    value={t.status}
                    onChange={(e) => onStatus(t, e.target.value as Todo["status"])}
                    aria-label="Status"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <span className={`status-dot ${STATUS_DOT[t.status]}`} />{" "}
                  <span className="mono muted">{t.id}</span> {t.title}
                </td>
                <td className="mono">
                  {t.due ? (
                    <span className={overdue ? "overdue" : ""}>{t.due}</span>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{t.squad ?? "—"}</td>
                <td>
                  {t.links.length === 0
                    ? "—"
                    : t.links.map((l) => (
                        <span
                          key={l.id}
                          className="link-chip mono"
                          title={l.title ?? "link pendente"}
                        >
                          {l.id}
                        </span>
                      ))}
                </td>
                <td>
                  <div className="step-actions">
                    <button className="btn-sm" onClick={() => onEdit(t)}>
                      Editar
                    </button>
                    <button className="btn-sm danger" onClick={() => onDelete(t)}>
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function TodoModal({
  todo,
  onClose,
  onSaved,
  onError,
}: {
  todo: Todo | null;
  onClose: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [title, setTitle] = useState(todo?.title ?? "");
  const [status, setStatus] = useState<Todo["status"]>(todo?.status ?? "open");
  const [due, setDue] = useState(todo?.due ?? "");
  const [squad, setSquad] = useState(todo?.squad ?? "");
  const [links, setLinks] = useState((todo?.links ?? []).map((l) => l.id).join(", "));
  const [saving, setSaving] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  async function save() {
    if (!title.trim()) return;
    setSaving(true);
    const body = {
      title: title.trim(),
      status,
      due: due || null,
      squad: squad.trim() || null,
      links: links
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };
    try {
      if (todo) await api.updateTodo(todo.id, body);
      else await api.createTodo(body);
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  }

  return (
    <Modal
      title={todo ? `Editar ${todo.id}` : "Novo afazer"}
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button className="primary" onClick={() => void save()} disabled={saving || !title.trim()}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </>
      }
    >
      <form
        className="modal-field"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <label htmlFor="todo-title">Título</label>
        <input
          id="todo-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Revisar regressão do checkout"
        />
      </form>
      <div className="field-grid">
        <div className="field col-6">
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value as Todo["status"])}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-6">
          <label>Prazo</label>
          <input type="date" value={due} onChange={(e) => setDue(e.target.value)} />
        </div>
        <div className="field col-6">
          <label>Squad (opcional)</label>
          <input value={squad} onChange={(e) => setSquad(e.target.value)} placeholder="pagamentos" />
        </div>
        <div className="field col-6">
          <label>Links (IDs, vírgula)</label>
          <input
            className="mono"
            value={links}
            onChange={(e) => setLinks(e.target.value)}
            placeholder="CT-0001, EXEC-0002, ST-0003"
          />
        </div>
      </div>
    </Modal>
  );
}
