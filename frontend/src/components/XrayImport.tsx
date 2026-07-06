import { useState } from "react";

const BASE = "/api/v1";

interface PreviewTest {
  external_key: string;
  title: string;
  priority: string;
  labels: string[];
  steps: number;
  story_key: string | null;
  action: string;
  existing_id: string | null;
  unmapped: string[];
}

interface PreviewData {
  tests: PreviewTest[];
  stories: { external_key: string; exists_locally: boolean }[];
}

interface ConfirmResult {
  created: { external_key: string; id: string }[];
  skipped: { external_key: string; id: string }[];
  stories_created: Record<string, string>;
}

async function postXml<T>(url: string, file: File, extra?: Record<string, string>): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  for (const [key, value] of Object.entries(extra ?? {})) form.append(key, value);
  const resp = await fetch(url, { method: "POST", body: form });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.error?.message ?? `${resp.status}`);
  return data as T;
}

export function XrayImport({
  onImported,
  onError,
}: {
  onImported: () => void;
  onError: (message: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [folder, setFolder] = useState("xray");
  const [chosenStories, setChosenStories] = useState<Set<string>>(new Set());
  const [result, setResult] = useState<ConfirmResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function doPreview(selected: File) {
    setBusy(true);
    setResult(null);
    try {
      const data = await postXml<PreviewData>(`${BASE}/import/xray`, selected);
      setPreview(data);
      setChosenStories(
        new Set(data.stories.filter((s) => !s.exists_locally).map((s) => s.external_key)),
      );
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }

  async function doConfirm() {
    if (!file) return;
    setBusy(true);
    try {
      const data = await postXml<ConfirmResult>(`${BASE}/import/xray/confirm`, file, {
        folder,
        create_stories: [...chosenStories].join(","),
      });
      setResult(data);
      setPreview(null);
      onImported();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="editor">
      <h2>Migração Xray</h2>
      <p className="muted" style={{ marginBottom: 12 }}>
        Ferramenta de migração pontual: envie o XML de export do Xray,
        revise o preview (nada é gravado) e confirme. Reimportar o mesmo
        XML é seguro — CTs já migrados são detectados por chave externa e
        pulados.
      </p>

      <div className="step-row" style={{ marginBottom: 12 }}>
        <input
          type="file"
          accept=".xml,text/xml"
          onChange={(e) => {
            const selected = e.target.files?.[0] ?? null;
            setFile(selected);
            if (selected) void doPreview(selected);
          }}
        />
        {busy && <span className="muted">Processando…</span>}
      </div>

      {preview && (
        <>
          <h3 className="section-title">Preview — {preview.tests.length} testes</h3>
          <div className="table-wrap">
          <table className="dense">
            <thead>
              <tr>
                <th>Chave</th>
                <th>Título</th>
                <th>Prioridade</th>
                <th>Steps</th>
                <th>Tags</th>
                <th>Story</th>
                <th>Ação</th>
                <th>Não mapeado</th>
              </tr>
            </thead>
            <tbody>
              {preview.tests.map((test) => (
                <tr key={test.external_key}>
                  <td className="mono">{test.external_key}</td>
                  <td>{test.title}</td>
                  <td>{test.priority}</td>
                  <td>{test.steps}</td>
                  <td>{test.labels.join(", ") || "—"}</td>
                  <td className="mono">{test.story_key ?? "—"}</td>
                  <td>
                    {test.action}
                    {test.existing_id ? ` (${test.existing_id})` : ""}
                  </td>
                  <td className="muted">{test.unmapped.join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>

          {preview.stories.length > 0 && (
            <>
              <h3 className="section-title">Stories vinculadas</h3>
              {preview.stories.map((story) => (
                <label key={story.external_key} className="step-row">
                  <input
                    type="checkbox"
                    style={{ width: "auto" }}
                    disabled={story.exists_locally}
                    checked={story.exists_locally || chosenStories.has(story.external_key)}
                    onChange={(e) => {
                      setChosenStories((old) => {
                        const next = new Set(old);
                        if (e.target.checked) next.add(story.external_key);
                        else next.delete(story.external_key);
                        return next;
                      });
                    }}
                  />
                  <span className="mono">{story.external_key}</span>
                  <span className="muted">
                    {story.exists_locally
                      ? "já existe localmente (será vinculada)"
                      : "criar story local espelho"}
                  </span>
                </label>
              ))}
            </>
          )}

          <div className="field" style={{ maxWidth: 320, margin: "12px 0" }}>
            <label>Pasta de destino (sob testcases/)</label>
            <input value={folder} onChange={(e) => setFolder(e.target.value)} />
          </div>
          <button className="primary" onClick={() => void doConfirm()} disabled={busy}>
            Confirmar migração
          </button>
        </>
      )}

      {result && (
        <div style={{ marginTop: 12 }}>
          <h3 className="section-title">Resultado</h3>
          <p>
            {result.created.length} CT{result.created.length === 1 ? "" : "s"} criado
            {result.created.length === 1 ? "" : "s"}
            {result.skipped.length > 0 &&
              `, ${result.skipped.length} pulado(s) — já migrados`}
            {Object.keys(result.stories_created).length > 0 &&
              `, stories: ${Object.entries(result.stories_created)
                .map(([k, v]) => `${k} → ${v}`)
                .join(", ")}`}
            .
          </p>
        </div>
      )}
    </div>
  );
}
