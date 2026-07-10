import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { LinksInput, MentionTextarea } from "./Autocomplete";
import { ConfirmModal, Modal } from "./Modal";
import { DocBody } from "./ReadView";
import type { Todo } from "../types";

const STATUS_DOT: Record<string, string> = {
  open: "dot-col-pending",
  doing: "dot-col-in_progress",
  blocked: "dot-col-blocked",
  done: "dot-col-passed",
};
const STATUSES: Todo["status"][] = ["open", "doing", "blocked", "done"];

export function Todos({
  onError,
  onNavigate,
}: {
  onError: (message: string) => void;
  onNavigate: (id: string) => void;
}) {
  const [items, setItems] = useState<Todo[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [bodies, setBodies] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<Todo | "new" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Todo | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);

  const query = useCallback(() => {
    const p = new URLSearchParams();
    if (statusFilter) p.set("status", statusFilter);
    if (dueFrom) p.set("due_from", dueFrom);
    if (dueTo) p.set("due_to", dueTo);
    const s = p.toString();
    return s ? `?${s}` : "";
  }, [statusFilter, dueFrom, dueTo]);

  const load = useCallback(() => {
    api
      .todos(query())
      .then((data) => {
        setItems(data);
        setSelected((old) => new Set([...old].filter((id) => data.some((t) => t.id === id))));
      })
      .catch((e) => onError(e.message));
  }, [query, onError]);

  useEffect(() => {
    load();
  }, [load]);

  function toggleSelect(id: string) {
    setSelected((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function toggleExpand(t: Todo) {
    setExpanded((old) => {
      const next = new Set(old);
      if (next.has(t.id)) next.delete(t.id);
      else next.add(t.id);
      return next;
    });
    if (!bodies[t.id]) {
      try {
        const full = await api.todo(t.id);
        setBodies((old) => ({ ...old, [t.id]: full.body ?? "" }));
      } catch {
        /* silencioso */
      }
    }
  }

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

  async function removeSelected() {
    setConfirmBulk(false);
    try {
      await Promise.all([...selected].map((id) => api.deleteTodo(id)));
      setSelected(new Set());
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const active = items.filter((t) => t.status !== "done");
  const done = items.filter((t) => t.status === "done");
  const today = new Date().toISOString().slice(0, 10);
  const exportParams: Record<string, string> = {};
  if (selected.size) {
    exportParams.ids = [...selected].join(",");
  } else {
    if (statusFilter) exportParams.status = statusFilter;
    if (dueFrom) exportParams.due_from = dueFrom;
    if (dueTo) exportParams.due_to = dueTo;
  }

  const rowProps = {
    today,
    selected,
    expanded,
    bodies,
    editDisabled: selected.size > 1,
    onSelect: toggleSelect,
    onExpand: toggleExpand,
    onEdit: setEditing,
    onDelete: setConfirmDelete,
    onStatus: quickStatus,
    onNavigate,
  };

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
          <label className="caption">Prazo</label>
          <input type="date" value={dueFrom} onChange={(e) => setDueFrom(e.target.value)} title="de" />
          <input type="date" value={dueTo} onChange={(e) => setDueTo(e.target.value)} title="até" />
          <a className="button-link" href={api.todosExportUrl("md", exportParams)} download>
            Export MD
          </a>
          <a className="button-link" href={api.todosExportUrl("xml", exportParams)} download>
            Export XML
          </a>
          <button className="primary" onClick={() => setEditing("new")}>
            Novo afazer
          </button>
        </div>
      </div>

      {selected.size > 0 && (
        <div className="bulk-bar">
          <span>{selected.size} selecionado(s)</span>
          <span className="spacer" style={{ flex: 1 }} />
          <button onClick={() => setSelected(new Set())}>Limpar seleção</button>
          <button className="danger" onClick={() => setConfirmBulk(true)}>
            Excluir selecionados ({selected.size})
          </button>
        </div>
      )}

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-title">Nenhum afazer</div>
          <div className="empty-body">
            Crie afazeres com prazo, status e links para CTs, execuções ou stories.
            Expanda para ver a descrição; impedimentos (blocked) entram na daily.
          </div>
        </div>
      ) : (
        <>
          {active.length > 0 && <TodoTable rows={active} {...rowProps} />}
          {done.length > 0 && (
            <>
              <h3 className="section-title">Concluídos ({done.length})</h3>
              <TodoTable rows={done} {...rowProps} />
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
            setBodies({});
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
      {confirmBulk && (
        <ConfirmModal
          title="Excluir vários afazeres"
          message={
            <>
              Tem certeza? Isso irá excluir <strong>{selected.size}</strong>{" "}
              {selected.size === 1 ? "item" : "itens"}.
            </>
          }
          confirmLabel={`Excluir ${selected.size} item(ns)`}
          danger
          onConfirm={() => void removeSelected()}
          onCancel={() => setConfirmBulk(false)}
        />
      )}
    </div>
  );
}

type RowProps = {
  today: string;
  selected: Set<string>;
  expanded: Set<string>;
  bodies: Record<string, string>;
  editDisabled: boolean;
  onSelect: (id: string) => void;
  onExpand: (t: Todo) => void;
  onEdit: (t: Todo) => void;
  onDelete: (t: Todo) => void;
  onStatus: (t: Todo, s: Todo["status"]) => void;
  onNavigate: (id: string) => void;
};

/** Cards estilo bloco de anotações (doc §1.4) — substitui a tabela. */
function TodoTable({ rows, ...p }: { rows: Todo[] } & RowProps) {
  return (
    <div className="todo-cards">
      {rows.map((t) => {
        const overdue = t.due && t.status !== "done" && t.due < p.today;
        const isOpen = p.expanded.has(t.id);
        const isSelected = p.selected.has(t.id);
        return (
          <div
            key={t.id}
            className={`todo-card note-${t.status} ${isSelected ? "selected" : ""}`}
          >
            <div className="todo-card-head">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => p.onSelect(t.id)}
                aria-label={`Selecionar ${t.id}`}
              />
              <span className="mono muted">{t.id}</span>
              <span className="spacer" style={{ flex: 1 }} />
              <select
                className="status-select"
                value={t.status}
                onChange={(e) => p.onStatus(t, e.target.value as Todo["status"])}
                aria-label="Status"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <button className="todo-card-title" onClick={() => p.onExpand(t)} title={t.title}>
              <span className={`status-dot ${STATUS_DOT[t.status]}`} /> {t.title}
            </button>

            <div className="todo-card-meta">
              {t.due && (
                <span className={`mono caption ${overdue ? "overdue" : "muted"}`}>
                  📅 {t.due}
                </span>
              )}
              {t.squad && <span className="caption muted">{t.squad}</span>}
            </div>

            {t.links.length > 0 && (
              <div className="todo-card-links">
                {t.links.map((l) => (
                  <button
                    key={l.id}
                    type="button"
                    className="link-chip mono link-chip-btn"
                    title={l.title ?? "link pendente (não encontrado)"}
                    onClick={() => p.onNavigate(l.id)}
                    disabled={!l.kind}
                  >
                    {l.id}
                  </button>
                ))}
              </div>
            )}

            {isOpen && (
              <div className="todo-card-body">
                {p.bodies[t.id]?.trim() ? (
                  <DocBody text={p.bodies[t.id]} onMention={p.onNavigate} />
                ) : (
                  <p className="muted caption">Sem descrição. Use Editar para adicionar.</p>
                )}
              </div>
            )}

            <div className="todo-card-actions">
              <button className="expand-btn" onClick={() => p.onExpand(t)} title="Descrição">
                {isOpen ? "▾" : "▸"}
              </button>
              <span className="spacer" style={{ flex: 1 }} />
              <button
                className="btn-sm"
                onClick={() => p.onEdit(t)}
                disabled={p.editDisabled}
                title={p.editDisabled ? "Desmarque para editar um item" : "Editar"}
              >
                Editar
              </button>
              <button className="btn-sm danger" onClick={() => p.onDelete(t)}>
                Excluir
              </button>
            </div>
          </div>
        );
      })}
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
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (todo) {
      api
        .todo(todo.id)
        .then((full) => setDescription(full.body ?? ""))
        .catch(() => {});
    }
  }, [todo]);

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
      body: description,
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
      <div className="modal-field">
        <label htmlFor="todo-title">Título</label>
        <input
          id="todo-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Revisar regressão do checkout"
        />
      </div>
      <div className="field-grid">
        <div className="field col-4">
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value as Todo["status"])}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-4">
          <label>Prazo</label>
          <input type="date" value={due} onChange={(e) => setDue(e.target.value)} />
        </div>
        <div className="field col-4">
          <label>Squad</label>
          <input value={squad} onChange={(e) => setSquad(e.target.value)} placeholder="pagamentos" />
        </div>
      </div>
      <div className="modal-field">
        <label htmlFor="todo-links">Links (IDs, vírgula)</label>
        <LinksInput id="todo-links" value={links} onChange={setLinks} />
      </div>
      <div className="modal-field">
        <label>Descrição — digite @ para referenciar um documento</label>
        <MentionTextarea
          value={description}
          onChange={setDescription}
          placeholder="Detalhes do afazer. Ex.: bloqueado por @CT-0007…"
        />
      </div>
    </Modal>
  );
}
