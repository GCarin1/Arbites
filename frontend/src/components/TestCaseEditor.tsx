import { useEffect, useState } from "react";
import { api } from "../api";
import type { TestCase } from "../types";

export function TestCaseEditor({
  id,
  onChanged,
  onDeleted,
}: {
  id: string;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const [mode, setMode] = useState<"form" | "raw">("form");
  const [tc, setTc] = useState<TestCase | null>(null);
  const [raw, setRaw] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    setMode("form");
    api
      .testcase(id)
      .then(setTc)
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    if (mode === "raw") {
      api
        .testcaseRaw(id)
        .then(setRaw)
        .catch((e) => setError(e.message));
    }
  }, [mode, id]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!tc) return <p className="empty">Carregando {id}…</p>;

  function set<K extends keyof TestCase>(key: K, value: TestCase[K]) {
    setTc((old) => (old ? { ...old, [key]: value } : old));
  }

  async function save() {
    if (!tc) return;
    setSaving(true);
    setError(null);
    try {
      if (mode === "raw") {
        const updated = await api.putTestcaseRaw(id, raw);
        setTc(updated);
      } else {
        const updated = await api.updateTestcase(id, {
          title: tc.title,
          type: tc.type,
          priority: tc.priority,
          status: tc.status,
          story: tc.story_id || null,
          tags: tc.tags ?? [],
          body: tc.body ?? "",
        });
        setTc(updated);
      }
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
      await api.deleteTestcase(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      <h2>
        <span className="mono muted">{tc.id}</span>
        <span>{tc.title}</span>
        <span className={`status-dot dot-${tc.status} muted`}>{tc.status}</span>
      </h2>
      <div className="toolbar">
        <button className={mode === "form" ? "primary" : ""} onClick={() => setMode("form")}>
          Formulário
        </button>
        <button className={mode === "raw" ? "primary" : ""} onClick={() => setMode("raw")}>
          Markdown cru
        </button>
        <span style={{ flex: 1 }} />
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar"}
        </button>
        <button className="danger" onClick={() => void remove()}>
          Excluir
        </button>
      </div>

      {mode === "raw" ? (
        <textarea
          className="raw"
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          spellCheck={false}
        />
      ) : (
        <>
          <div className="field-grid">
            <div className="field wide">
              <label>Título</label>
              <input value={tc.title} onChange={(e) => set("title", e.target.value)} />
            </div>
            <div className="field">
              <label>Tipo</label>
              <select
                value={tc.type}
                onChange={(e) => set("type", e.target.value as TestCase["type"])}
              >
                <option value="manual">manual</option>
                <option value="automated">automated</option>
                <option value="hybrid">hybrid</option>
              </select>
            </div>
            <div className="field">
              <label>Prioridade</label>
              <select value={tc.priority} onChange={(e) => set("priority", e.target.value)}>
                <option value="critical">critical</option>
                <option value="high">high</option>
                <option value="medium">medium</option>
                <option value="low">low</option>
              </select>
            </div>
            <div className="field">
              <label>Status</label>
              <select value={tc.status} onChange={(e) => set("status", e.target.value)}>
                <option value="draft">draft</option>
                <option value="ready">ready</option>
                <option value="deprecated">deprecated</option>
              </select>
            </div>
            <div className="field">
              <label>Story</label>
              <input
                className="mono"
                placeholder="ST-0000"
                value={tc.story_id ?? ""}
                onChange={(e) => set("story_id", e.target.value || null)}
              />
            </div>
            <div className="field">
              <label>Tags (vírgula)</label>
              <input
                value={(tc.tags ?? []).join(", ")}
                onChange={(e) =>
                  set(
                    "tags",
                    e.target.value
                      .split(",")
                      .map((t) => t.trim())
                      .filter(Boolean),
                  )
                }
              />
            </div>
            <div className="field">
              <label>Arquivo</label>
              <span className="mono muted" style={{ padding: "4px 0" }}>
                {tc.path}
              </span>
            </div>
          </div>
          <div className="field wide">
            <label>Corpo (markdown — Objetivo / Pré-condições / Passos / Resultado esperado)</label>
            <textarea
              className="raw"
              value={tc.body ?? ""}
              onChange={(e) => set("body", e.target.value)}
              spellCheck={false}
            />
          </div>
        </>
      )}
    </div>
  );
}
