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
