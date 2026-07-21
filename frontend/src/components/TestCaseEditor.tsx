import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { SingleRefInput } from "./Autocomplete";
import { ConfirmModal } from "./Modal";
import { DetailCard, DocBody, ReadField } from "./ReadView";
import { useToast } from "./Toast";
import type { Criterion, TestCase, TestCaseResult } from "../types";

export function TestCaseEditor({
  id,
  onChanged,
  onDeleted,
}: {
  id: string;
  onChanged: () => void;
  onDeleted: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [mode, setMode] = useState<"form" | "raw">("form");
  const [tc, setTc] = useState<TestCase | null>(null);
  const [raw, setRaw] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [history, setHistory] = useState<TestCaseResult[]>([]);
  const [storyCriteria, setStoryCriteria] = useState<Criterion[]>([]); // 0092
  const [isFlaky, setIsFlaky] = useState(false); // 0089: alternância recente
  const { toast } = useToast();

  // critérios EARS da story vinculada (para o picker de vínculo criteria↔CT)
  useEffect(() => {
    const story = tc?.story_id;
    if (!story) {
      setStoryCriteria([]);
      return;
    }
    let alive = true;
    api
      .requirementCriteria(story)
      .then((c) => alive && setStoryCriteria(c))
      .catch(() => alive && setStoryCriteria([]));
    return () => {
      alive = false;
    };
  }, [tc?.story_id]);

  const load = useCallback(() => {
    setError(null);
    api
      .testcaseResults(id)
      .then(setHistory)
      .catch(() => {});
    api
      .metricsFlaky(5)
      .then((f) => setIsFlaky(f.testcases.some((t) => t.testcase_id === id)))
      .catch(() => setIsFlaky(false));
    return api
      .testcase(id)
      .then(setTc)
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    setMode("form");
    setEditing(false); // sempre abre em modo leitura
    void load();
  }, [id, load]);

  useEffect(() => {
    if (editing && mode === "raw") {
      api
        .testcaseRaw(id)
        .then(setRaw)
        .catch((e) => setError(e.message));
    }
  }, [editing, mode, id]);

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
          squad: tc.squad || null,
          quarantine: tc.quarantine ?? false,
          tags: tc.tags ?? [],
          criteria: tc.criteria ?? [],
          body: tc.body ?? "",
        });
        setTc(updated);
      }
      setEditing(false); // após salvar, volta ao modo leitura
      toast("Caso de teste salvo");
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function cancelEdit() {
    void load(); // descarta edições não salvas
    setMode("form");
    setEditing(false);
  }

  async function remove() {
    setConfirmDelete(false);
    try {
      await api.deleteTestcase(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      {confirmDelete && (
        <ConfirmModal
          title="Excluir test case"
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
            id={tc.id}
            title={tc.title}
            status={
              <span className="tc-badges">
                <span className={`status-dot dot-${tc.status}`}>{tc.status}</span>
                {isFlaky && (
                  <span
                    className="badge badge-flaky"
                    title="Resultado alternou pass/fail nas últimas execuções"
                  >
                    flaky
                  </span>
                )}
                {tc.quarantine && (
                  <span
                    className="badge badge-quarantine"
                    title="Em quarentena — fora do pass rate e da cobertura"
                  >
                    quarentena
                  </span>
                )}
                {tc.needs_rerun && (
                  <span
                    className="badge badge-rerun"
                    title="Steps re-baseados na sync — precisa re-execução"
                  >
                    precisa re-execução
                  </span>
                )}
              </span>
            }
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
            <ReadField label="Tipo" value={tc.type} />
            <ReadField label="Prioridade" value={tc.priority} />
            <ReadField
              label="Status"
              value={<span className={`status-dot dot-${tc.status}`}>{tc.status}</span>}
            />
            <ReadField label="Story" value={tc.story_id} mono />
            <ReadField
              label="Critérios EARS"
              value={(tc.criteria ?? []).length ? (tc.criteria ?? []).join(", ") : null}
              mono
            />
            <ReadField
              label="Squad"
              value={
                tc.squad_effective ? (
                  <>
                    {tc.squad_effective}
                    {!tc.squad && <span className="muted"> (herdado)</span>}
                  </>
                ) : null
              }
            />
            <ReadField
              label="Tags"
              value={(tc.tags ?? []).length ? (tc.tags ?? []).join(", ") : null}
            />
            <ReadField label="Arquivo" value={tc.path} mono />
          </div>
          </DetailCard>
          <div className="card">
            <div className="card-head">
              <h3>Corpo</h3>
            </div>
            <DocBody text={tc.body} />
          </div>
          {history.length > 0 && (
            <div className="card" style={{ marginTop: 16 }}>
              <div className="card-head">
                <h3>Histórico de resultados</h3>
                <span className="spacer" />
                <span className="caption muted">
                  {history.length} execução{history.length === 1 ? "" : "ões"}
                </span>
              </div>
              <div className="tc-history-dots" title="mais recente à esquerda">
                {history.slice(0, 20).map((h, i) => (
                  <span
                    key={i}
                    className={`status-dot dot-col-${h.status} caption`}
                    title={`${h.execution_id} · ${h.status}`}
                  />
                ))}
              </div>
              <div className="table-wrap">
                <table className="dense">
                  <thead>
                    <tr>
                      <th>Execução</th>
                      <th>Status</th>
                      <th>Quando</th>
                      <th>Duração</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h, i) => (
                      <tr key={i}>
                        <td className="mono">{h.execution_id}</td>
                        <td>
                          <span className={`status-dot dot-col-${h.status} caption`}>
                            {h.status}
                          </span>
                        </td>
                        <td className="caption muted">
                          {(h.executed_at ?? "").slice(0, 16).replace("T", " ") || "—"}
                        </td>
                        <td className="caption muted">
                          {h.duration_seconds !== null ? `${h.duration_seconds}s` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
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
            <span className="spacer" />
            <button className="primary" onClick={() => void save()} disabled={saving}>
              {saving ? "Salvando…" : "Salvar"}
            </button>
            <button onClick={cancelEdit} disabled={saving}>
              Cancelar
            </button>
            <button className="danger" onClick={() => setConfirmDelete(true)}>
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
              <label>Story (digite id ou título)</label>
              <SingleRefInput
                id="tc-story"
                value={tc.story_id ?? ""}
                onChange={(v) => set("story_id", v || null)}
                kinds="requirement"
                placeholder="ST-0000 — digite para sugerir"
              />
            </div>
            <div className="field">
              <label>Squad (vazio = herda da story)</label>
              <input
                placeholder="ex.: pagamentos"
                value={tc.squad ?? ""}
                onChange={(e) => set("squad", e.target.value || null)}
              />
            </div>
            <div className="field">
              <label>Quarentena</label>
              <label className="check-inline">
                <input
                  type="checkbox"
                  checked={tc.quarantine ?? false}
                  onChange={(e) => set("quarantine", e.target.checked)}
                />
                <span>Excluir do pass rate e da cobertura (contado no dashboard)</span>
              </label>
            </div>
            {storyCriteria.length > 0 && (
              <div className="field wide">
                <label>Critérios EARS cobertos (da story)</label>
                <div className="criteria-picker">
                  {storyCriteria.map((c) => {
                    const checked = (tc.criteria ?? []).includes(c.ears_id);
                    return (
                      <label key={c.ears_id} className="check-inline caption">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() =>
                            set(
                              "criteria",
                              checked
                                ? (tc.criteria ?? []).filter((x) => x !== c.ears_id)
                                : [...(tc.criteria ?? []), c.ears_id],
                            )
                          }
                        />
                        <span className="mono">{c.ears_id}</span>
                        <span className="muted">{c.text}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
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
              <span className="path-value" title={tc.path}>
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
        </>
      )}
    </div>
  );
}
