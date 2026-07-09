import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { ConfirmModal, Modal } from "./Modal";
import { DetailCard, DocBody, ReadField } from "./ReadView";
import type { Requirement } from "../types";

export function RequirementsList({
  version,
  selected,
  onSelect,
  onCreated,
  onError,
}: {
  version: number;
  selected: string | null;
  onSelect: (id: string) => void;
  onCreated: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [items, setItems] = useState<Requirement[]>([]);
  const [creating, setCreating] = useState<"epic" | "story" | null>(null);

  useEffect(() => {
    api
      .requirements()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [version, onError]);

  async function create(kind: "epic" | "story", title: string, epic: string | null) {
    try {
      const created = await api.createRequirement({ kind, title, epic });
      setCreating(null);
      onCreated(created.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const epics = items.filter((r) => r.kind === "epic");
  const stories = items.filter((r) => r.kind === "story");
  const orphans = stories.filter((s) => !epics.some((e) => e.id === s.epic_id));

  return (
    <div>
      <div className="list-toolbar">
        <button onClick={() => setCreating("epic")}>Novo epic</button>
        <button onClick={() => setCreating("story")}>Nova story</button>
      </div>
      {creating && (
        <NewRequirementModal
          kind={creating}
          onSubmit={(title, epic) => void create(creating, title, epic)}
          onClose={() => setCreating(null)}
        />
      )}
      {epics.map((epic) => (
        <div key={epic.id}>
          <ReqItem item={epic} selected={selected} onSelect={onSelect} />
          <div style={{ paddingLeft: 16 }}>
            {stories
              .filter((s) => s.epic_id === epic.id)
              .map((story) => (
                <ReqItem key={story.id} item={story} selected={selected} onSelect={onSelect} />
              ))}
          </div>
        </div>
      ))}
      {orphans.length > 0 && (
        <>
          <div className="dir mono" style={{ paddingTop: 8 }}>
            sem epic/
          </div>
          {orphans.map((story) => (
            <ReqItem key={story.id} item={story} selected={selected} onSelect={onSelect} />
          ))}
        </>
      )}
      {items.length === 0 && <p className="muted">Nenhum requisito ainda.</p>}
    </div>
  );
}

/**
 * Repositório de requisitos centralizado (doc §1.2) — hierarquia epic→story
 * com expandir/colapsar, drag & drop de story para outro epic (reassocia),
 * exclusão com confirmação e data de criação. Detalhe abre só por clique.
 */
export function ReqRepository({
  version,
  onOpen,
  onChanged,
  onError,
}: {
  version: number;
  onOpen: (id: string) => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [items, setItems] = useState<Requirement[]>([]);
  const [creating, setCreating] = useState<"epic" | "story" | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [dragStory, setDragStory] = useState<string | null>(null);
  const [dropEpic, setDropEpic] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<Requirement | null>(null);

  const load = useCallback(() => {
    api
      .requirements()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    load();
  }, [load, version]);

  async function create(kind: "epic" | "story", title: string, epic: string | null) {
    try {
      const created = await api.createRequirement({ kind, title, epic });
      setCreating(null);
      onChanged();
      onOpen(created.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function moveStory(epicId: string | null) {
    if (!dragStory) return;
    try {
      await api.updateRequirement(dragStory, { epic: epicId });
      onChanged();
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setDragStory(null);
      setDropEpic(null);
    }
  }

  async function remove(item: Requirement) {
    setDeleting(null);
    try {
      await api.deleteRequirement(item.id);
      onChanged();
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function toggle(id: string) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const epics = items.filter((r) => r.kind === "epic");
  const stories = items.filter((r) => r.kind === "story");
  const orphans = stories.filter((s) => !epics.some((e) => e.id === s.epic_id));

  const storyRow = (story: Requirement) => (
    <div
      key={story.id}
      className={`repo-row repo-file ${dragStory === story.id ? "dragging" : ""}`}
      style={{ paddingLeft: 28 }}
      draggable
      onDragStart={() => setDragStory(story.id)}
      onDragEnd={() => {
        setDragStory(null);
        setDropEpic(null);
      }}
    >
      <button className="repo-file-main" onClick={() => onOpen(story.id)}>
        <span className="mono muted">{story.id}</span>
        <span className="repo-file-title">{story.title}</span>
      </button>
      <span className={`status-dot dot-${story.status} caption`}>{story.status}</span>
      <span className="caption mono muted">{story.created ?? ""}</span>
      <span className="repo-actions">
        <button className="btn-sm danger" onClick={() => setDeleting(story)}>
          Excluir
        </button>
      </span>
    </div>
  );

  return (
    <div className="repo">
      <div className="page-head">
        <h1 className="page-title">Requisitos</h1>
        <span className="spacer" />
        <div className="head-controls">
          <button onClick={() => setCreating("epic")}>Novo epic</button>
          <button className="primary" onClick={() => setCreating("story")}>
            Nova story
          </button>
        </div>
      </div>

      <div className="repo-tree card">
        {items.length === 0 ? (
          <div className="empty-state" style={{ border: "none" }}>
            <div className="empty-title">Nenhum requisito</div>
            <div className="empty-body">
              Crie epics e stories. Arraste uma story para outro epic para
              reassociá-la.
            </div>
          </div>
        ) : (
          <>
            {epics.map((epic) => {
              const isCollapsed = collapsed.has(epic.id);
              const children = stories.filter((s) => s.epic_id === epic.id);
              return (
                <div key={epic.id} className="repo-dir">
                  <div
                    className={`repo-row repo-folder ${dropEpic === epic.id ? "drop-target" : ""}`}
                    onDragOver={(e) => {
                      if (dragStory) {
                        e.preventDefault();
                        setDropEpic(epic.id);
                      }
                    }}
                    onDragLeave={() => setDropEpic((t) => (t === epic.id ? null : t))}
                    onDrop={() => void moveStory(epic.id)}
                  >
                    <button className="expand-btn" onClick={() => toggle(epic.id)}>
                      {isCollapsed ? "▸" : "▾"}
                    </button>
                    <button className="repo-file-main" onClick={() => onOpen(epic.id)}>
                      <span className="mono muted">{epic.id}</span>
                      <span className="repo-folder-name">{epic.title}</span>
                    </button>
                    <span className="caption muted">{children.length}</span>
                    <span className="caption mono muted">{epic.created ?? ""}</span>
                    <span className="repo-actions">
                      <button className="btn-sm danger" onClick={() => setDeleting(epic)}>
                        Excluir
                      </button>
                    </span>
                  </div>
                  {!isCollapsed && children.map(storyRow)}
                </div>
              );
            })}
            {orphans.length > 0 && (
              <div
                className={`repo-row repo-folder ${dropEpic === "__none__" ? "drop-target" : ""}`}
                onDragOver={(e) => {
                  if (dragStory) {
                    e.preventDefault();
                    setDropEpic("__none__");
                  }
                }}
                onDragLeave={() => setDropEpic((t) => (t === "__none__" ? null : t))}
                onDrop={() => void moveStory(null)}
              >
                <span className="repo-folder-name muted">sem epic/</span>
              </div>
            )}
            {orphans.map(storyRow)}
          </>
        )}
      </div>

      {creating && (
        <NewRequirementModal
          kind={creating}
          onSubmit={(title, epic) => void create(creating, title, epic)}
          onClose={() => setCreating(null)}
        />
      )}
      {deleting && (
        <ConfirmModal
          title={`Excluir ${deleting.kind === "epic" ? "epic" : "story"}`}
          message={
            <>
              Mover <span className="mono">{deleting.id}</span> ({deleting.title})
              para a lixeira?
              {deleting.kind === "epic" && " As stories dele ficam sem epic."}
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove(deleting)}
          onCancel={() => setDeleting(null)}
        />
      )}
    </div>
  );
}

function ReqItem({
  item,
  selected,
  onSelect,
}: {
  item: Requirement;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      className={`list-item ${item.id === selected ? "selected" : ""}`}
      onClick={() => onSelect(item.id)}
    >
      <span className="mono muted">{item.id}</span>
      <span>{item.title}</span>
    </button>
  );
}

function NewRequirementModal({
  kind,
  onSubmit,
  onClose,
}: {
  kind: "epic" | "story";
  onSubmit: (title: string, epic: string | null) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [epic, setEpic] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);
  const label = kind === "epic" ? "epic" : "story";

  function submit() {
    if (!title.trim()) return;
    onSubmit(title.trim(), kind === "story" ? epic.trim() || null : null);
  }

  return (
    <Modal
      title={`Novo ${label}`}
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose}>Cancelar</button>
          <button className="primary" onClick={submit} disabled={!title.trim()}>
            Criar
          </button>
        </>
      }
    >
      <form
        className="modal-field"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="new-req-title">Título</label>
        <input
          id="new-req-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={kind === "epic" ? "Ex.: Autenticação" : "Ex.: Login"}
        />
      </form>
      {kind === "story" && (
        <div className="modal-field">
          <label htmlFor="new-req-epic">Epic pai (opcional)</label>
          <input
            id="new-req-epic"
            className="mono"
            value={epic}
            onChange={(e) => setEpic(e.target.value)}
            placeholder="EP-0001 — vazio = nenhum"
          />
        </div>
      )}
    </Modal>
  );
}

export function RequirementEditor({
  id,
  onChanged,
  onDeleted,
}: {
  id: string;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const [req, setReq] = useState<Requirement | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const load = useCallback(() => {
    setError(null);
    return api
      .requirement(id)
      .then(setReq)
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    setEditing(false); // sempre abre em modo leitura
    void load();
  }, [id, load]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!req) return <p className="empty">Carregando {id}…</p>;

  function set<K extends keyof Requirement>(key: K, value: Requirement[K]) {
    setReq((old) => (old ? { ...old, [key]: value } : old));
  }

  async function save() {
    if (!req) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateRequirement(id, {
        title: req.title,
        status: req.status,
        epic: req.epic_id || null,
        external_key: req.external_key || null,
        confluence_url: req.confluence_url || null,
        squad: req.squad || null,
        tags: req.tags,
        body: req.body ?? "",
      });
      setReq(updated);
      setEditing(false); // após salvar, volta ao modo leitura
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    void load(); // descarta edições não salvas
    setEditing(false);
  }

  async function remove() {
    setConfirmDelete(false);
    try {
      await api.deleteRequirement(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      {confirmDelete && (
        <ConfirmModal
          title="Excluir requisito"
          message={
            <>
              Mover <span className="mono">{id}</span> para a lixeira
              (<span className="mono">.arbites/trash/</span>)?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove()}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
      {!editing ? (
        <>
          <DetailCard
            id={req.id}
            title={req.title}
            status={<span className={`status-dot dot-${req.status}`}>{req.status}</span>}
            actions={
              <>
                <button className="primary" onClick={() => setEditing(true)}>
                  Editar
                </button>
                <button className="danger" onClick={() => setConfirmDelete(true)}>
                  Excluir
                </button>
              </>
            }
          >
          <div className="read-grid">
            <ReadField label="Tipo" value={req.kind} />
            <ReadField
              label="Status"
              value={<span className={`status-dot dot-${req.status}`}>{req.status}</span>}
            />
            {req.kind === "story" && <ReadField label="Epic" value={req.epic_id} mono />}
            <ReadField label="Squad" value={req.squad} />
            <ReadField label="Chave externa" value={req.external_key} mono />
            {req.kind === "story" && (
              <ReadField
                label="Confluence"
                wide
                value={
                  req.confluence_url ? (
                    <a href={req.confluence_url} target="_blank" rel="noreferrer">
                      {req.confluence_url}
                    </a>
                  ) : null
                }
              />
            )}
            <ReadField
              label="Tags"
              value={(req.tags ?? []).length ? (req.tags ?? []).join(", ") : null}
            />
            <ReadField label="Arquivo" value={req.path} mono />
          </div>
          </DetailCard>
          <div className="card">
            <div className="card-head">
              <h3>Corpo</h3>
            </div>
            <DocBody text={req.body} />
          </div>
        </>
      ) : (
        <>
      <h2>
        <span className="mono muted">{req.id}</span>
        <span>{req.title}</span>
        <span className={`status-dot dot-${req.status} muted`}>{req.status}</span>
      </h2>
      <div className="toolbar">
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </button>
        <button onClick={cancelEdit} disabled={saving}>
          Cancelar
        </button>
        <span className="spacer" />
        <button className="danger" onClick={() => setConfirmDelete(true)}>
          Excluir
        </button>
      </div>
      <div className="field-grid">
        <div className="field wide">
          <label>Título</label>
          <input value={req.title} onChange={(e) => set("title", e.target.value)} />
        </div>
        <div className="field">
          <label>Status</label>
          <select value={req.status} onChange={(e) => set("status", e.target.value)}>
            <option value="active">active</option>
            <option value="done">done</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>
        <div className="field">
          <label>Squad</label>
          <input
            placeholder="ex.: pagamentos"
            value={req.squad ?? ""}
            onChange={(e) => set("squad", e.target.value || null)}
          />
        </div>
        {req.kind === "story" && (
          <div className="field">
            <label>Epic</label>
            <input
              className="mono"
              placeholder="EP-0000"
              value={req.epic_id ?? ""}
              onChange={(e) => set("epic_id", e.target.value || null)}
            />
          </div>
        )}
        <div className="field">
          <label>Chave externa</label>
          <input
            className="mono"
            placeholder="PROJ-123"
            value={req.external_key ?? ""}
            onChange={(e) => set("external_key", e.target.value || null)}
          />
        </div>
        {req.kind === "story" && (
          <div className="field wide">
            <label>Confluence URL</label>
            <input
              value={req.confluence_url ?? ""}
              onChange={(e) => set("confluence_url", e.target.value || null)}
            />
          </div>
        )}
      </div>
      <div className="field wide">
        <label>
          {req.kind === "story"
            ? "Corpo (Resumo / Critérios de aceite — EARS quando fizer sentido)"
            : "Corpo (Descrição)"}
        </label>
        <textarea
          className="raw"
          value={req.body ?? ""}
          onChange={(e) => set("body", e.target.value)}
          spellCheck={false}
        />
      </div>
        </>
      )}
    </div>
  );
}
