import { useEffect, useState } from "react";
import { api } from "../api";
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

  useEffect(() => {
    api
      .requirements()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [version, onError]);

  async function create(kind: "epic" | "story") {
    const title = window.prompt(`Título do novo ${kind}:`);
    if (!title) return;
    let epic: string | null = null;
    if (kind === "story") {
      epic = window.prompt("Epic pai (ex.: EP-0001 — vazio = nenhum):") || null;
    }
    try {
      const created = await api.createRequirement({ kind, title, epic });
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
      <div style={{ display: "flex", gap: 8, padding: "0 0 8px" }}>
        <button onClick={() => void create("epic")}>Novo epic</button>
        <button onClick={() => void create("story")}>Nova story</button>
      </div>
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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .requirement(id)
      .then(setReq)
      .catch((e) => setError(e.message));
  }, [id]);

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
        tags: req.tags,
        body: req.body ?? "",
      });
      setReq(updated);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Mover ${id} para a lixeira (.arbites/trash/)?`)) return;
    try {
      await api.deleteRequirement(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      <h2>
        <span className="mono muted">{req.id}</span>
        <span>{req.title}</span>
        <span className={`status-dot dot-${req.status} muted`}>{req.status}</span>
      </h2>
      <div className="toolbar">
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </button>
        <button className="danger" onClick={() => void remove()}>
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
    </div>
  );
}
