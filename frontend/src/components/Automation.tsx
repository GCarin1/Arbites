import { useCallback, useEffect, useRef, useState } from "react";

const BASE = "/api/v1";

interface Target {
  name: string;
  kind: string;
  local_path: string | null;
  features_glob: string | null;
  python_path: string | null;
  working_dir: string | null;
  timeout_minutes: number | null;
  scenarios: number;
  queue_length: number;
}

interface FoundFeature {
  path: string;
  scenarios: number;
  parseable: boolean;
}

interface TargetFeature {
  path: string;
  scenarios: number; // total de cenários no arquivo (do disco)
  mapped: number; // quantos têm tag reconhecida (vinculados a um CT)
}

interface RunSnapshot {
  exec_id: string;
  target: string;
  status: string;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  log_lines: number;
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.error?.message ?? `${resp.status}`);
  return data as T;
}

export function Automation({
  onChanged,
  onError,
}: {
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [selection, setSelection] = useState("");
  const [tags, setTags] = useState("");
  const [feature, setFeature] = useState("");
  const [features, setFeatures] = useState<TargetFeature[]>([]);
  const [knownTags, setKnownTags] = useState<string[]>([]);
  const [run, setRun] = useState<RunSnapshot | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const sourceRef = useRef<EventSource | null>(null);

  const loadTargets = useCallback(() => {
    json<Target[]>(`${BASE}/targets`)
      .then((data) => {
        setTargets(data);
        setSelection((old) => old || data[0]?.name || "");
      })
      .catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    loadTargets();
    return () => sourceRef.current?.close();
  }, [loadTargets]);

  // features + tags do target selecionado (dropdowns do comando behave)
  useEffect(() => {
    if (!selection) return;
    json<{ features: TargetFeature[]; tags: string[] }>(
      `${BASE}/targets/${selection}/features`,
    )
      .then((data) => {
        setFeatures(data.features);
        setKnownTags(data.tags);
      })
      .catch(() => {
        setFeatures([]);
        setKnownTags([]);
      });
  }, [selection]);

  async function scan(name: string) {
    try {
      await json(`${BASE}/targets/${name}/scan`, { method: "POST" });
      loadTargets();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function startRun() {
    if (!selection) return;
    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    try {
      const data = await json<{ execution: { id: string }; run: RunSnapshot }>(
        `${BASE}/runs/local`,
        {
          method: "POST",
          body: JSON.stringify({
            target: selection,
            tags: tagList,
            feature: feature || null,
          }),
        },
      );
      setRun(data.run);
      setLog([]);
      onChanged();
      sourceRef.current?.close();
      const source = new EventSource(`${BASE}/runs/${data.execution.id}/stream`);
      sourceRef.current = source;
      source.onmessage = (event) => setLog((old) => [...old, event.data]);
      source.addEventListener("done", (event) => {
        setRun((old) => (old ? { ...old, status: (event as MessageEvent).data } : old));
        source.close();
        onChanged();
        loadTargets();
      });
      source.onerror = () => source.close();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function cancelRun() {
    if (!run) return;
    try {
      const snapshot = await json<RunSnapshot>(`${BASE}/runs/${run.exec_id}/cancel`, {
        method: "POST",
      });
      setRun(snapshot);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const selectedFeature = feature ? features.find((f) => f.path === feature) : undefined;

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Automação</h1>
      </div>

      <TargetsCard targets={targets} onScan={scan} onSaved={loadTargets} onError={onError} />

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-head">
          <h3>Novo run local (Behave)</h3>
          <span className="spacer" />
          <span className="caption mono">
            behave {feature || "./features"} {tags.trim() ? `--tags=${tags}` : ""}
          </span>
        </div>
        <div className="field-grid">
          <div className="field col-3">
            <label>Target</label>
            <select value={selection} onChange={(e) => setSelection(e.target.value)}>
              {targets.map((target) => (
                <option key={target.name} value={target.name}>
                  {target.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field col-6">
            <label>Arquivo .feature (vazio = todos)</label>
            <select value={feature} onChange={(e) => setFeature(e.target.value)}>
              <option value="">(todos os features)</option>
              {features.map((f) => (
                <option key={f.path} value={f.path}>
                  {f.path} ({f.mapped < f.scenarios ? `${f.mapped}/${f.scenarios} mapeados` : f.scenarios})
                </option>
              ))}
            </select>
            {selectedFeature && selectedFeature.mapped === 0 && (
              <p className="caption muted" style={{ marginTop: 4 }}>
                Nenhum cenário deste arquivo está vinculado a um caso de
                teste (tag de CT no cenário). O Behave roda o arquivo
                inteiro normalmente, mas os resultados não aparecerão
                vinculados a um CT — tague os cenários para rastreabilidade.
              </p>
            )}
          </div>
          <div className="field col-3">
            <label>Tag (autocomplete)</label>
            <input
              list="behave-tags"
              placeholder="@smoke, @CT-0001"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
            <datalist id="behave-tags">
              {knownTags.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>
        </div>
        <div className="toolbar">
          <button
            className="primary"
            onClick={() => void startRun()}
            disabled={!selection || (!feature && !tags.trim())}
          >
            Rodar
          </button>
          {run && run.status === "running" && (
            <button className="danger" onClick={() => void cancelRun()}>
              Cancelar
            </button>
          )}
        </div>

        {run && (
          <>
            <h4 className="section-title">
              Run {run.exec_id} —{" "}
              <span className={`status-dot dot-col-${run.status === "done" ? "passed" : run.status === "running" ? "in_progress" : "failed"}`}>
                {run.status}
              </span>
            </h4>
            <pre className="run-log">
              {log.length > 0 ? log.join("\n") : "aguardando saída…"}
            </pre>
          </>
        )}
      </div>

      {selection && <ArtifactsCard target={selection} refreshKey={run?.status ?? ""} />}
      {selection && <EnvCard target={selection} onError={onError} />}

      <CIPanel targets={targets} onChanged={onChanged} onError={onError} />
    </div>
  );
}

// ---------------------------------------------------------------- CI (M4)

interface CIStatus {
  execution_id: string;
  workflow: {
    id: number;
    status: string;
    conclusion: string | null;
    html_url: string;
  };
  jobs: {
    name: string;
    status: string;
    conclusion: string | null;
    steps: { name: string; status: string; conclusion: string | null }[];
  }[];
  poll_interval_seconds: number;
}

// ------------------------------------------------------------ targets CRUD

const DEFAULT_GLOB = "features/**/*.feature";

function emptyTarget(): Target {
  return {
    name: "",
    kind: "behave",
    local_path: "",
    features_glob: DEFAULT_GLOB,
    python_path: null,
    working_dir: null,
    timeout_minutes: null,
    scenarios: 0,
    queue_length: 0,
  };
}

/**
 * CRUD de targets direto na UI — evita ter que abrir o arbites.yaml na mão.
 * "Adicionar/atualizar na lista" faz staging local; "Salvar configuração"
 * grava tudo de uma vez (PUT /targets), igual ao padrão de Providers de IA.
 */
function TargetsCard({
  targets,
  onScan,
  onSaved,
  onError,
}: {
  targets: Target[];
  onScan: (name: string) => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [staged, setStaged] = useState<Target[]>(targets);
  const [saving, setSaving] = useState(false);
  const [editingName, setEditingName] = useState<string | null>(null);
  const [form, setForm] = useState<Target>(emptyTarget());
  const [timeoutText, setTimeoutText] = useState("");
  const [browsing, setBrowsing] = useState(false);
  const [browseError, setBrowseError] = useState<string | null>(null);
  const [found, setFound] = useState<FoundFeature[] | null>(null);

  useEffect(() => {
    setStaged(targets);
  }, [targets]);

  function resetForm() {
    setEditingName(null);
    setForm(emptyTarget());
    setTimeoutText("");
    setFound(null);
    setBrowseError(null);
  }

  function editTarget(t: Target) {
    setEditingName(t.name);
    setForm({ ...t });
    setTimeoutText(t.timeout_minutes != null ? String(t.timeout_minutes) : "");
    setFound(null);
    setBrowseError(null);
  }

  function currentDraft(): Target | null {
    if (!form.name.trim() || !form.local_path?.trim()) return null;
    return {
      ...form,
      name: form.name.trim(),
      local_path: form.local_path.trim(),
      features_glob: form.features_glob?.trim() || DEFAULT_GLOB,
      python_path: form.python_path?.trim() || null,
      working_dir: form.working_dir?.trim() || null,
      timeout_minutes: timeoutText.trim() ? Number(timeoutText) : null,
    };
  }

  function stageTarget() {
    const draft = currentDraft();
    if (!draft) return;
    setStaged((old) => [...old.filter((x) => x.name !== draft.name), draft]);
    resetForm();
  }

  function removeTarget(name: string) {
    setStaged((old) => old.filter((x) => x.name !== name));
  }

  async function browse() {
    const localPath = form.local_path?.trim();
    if (!localPath) return;
    setBrowsing(true);
    setBrowseError(null);
    try {
      const params = new URLSearchParams({
        local_path: localPath,
        features_glob: form.features_glob?.trim() || DEFAULT_GLOB,
      });
      const data = await json<{ features: FoundFeature[] }>(
        `${BASE}/automation/browse-features?${params.toString()}`,
      );
      setFound(data.features);
    } catch (e) {
      setFound(null);
      setBrowseError(e instanceof Error ? e.message : String(e));
    } finally {
      setBrowsing(false);
    }
  }

  async function save() {
    setSaving(true);
    // inclui o que está no formulário mesmo sem "adicionar à lista" antes —
    // senão o usuário preenche, salva e nada persiste (mesmo cuidado do
    // form de providers de IA).
    const draft = currentDraft();
    const effStaged = draft
      ? [...staged.filter((x) => x.name !== draft.name), draft]
      : staged;
    try {
      await json(`${BASE}/targets`, {
        method: "PUT",
        body: JSON.stringify({
          targets: effStaged.map((t) => ({
            name: t.name,
            kind: t.kind,
            local_path: t.local_path,
            features_glob: t.features_glob,
            python_path: t.python_path,
            working_dir: t.working_dir,
            timeout_minutes: t.timeout_minutes,
          })),
        }),
      });
      resetForm();
      onSaved();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Targets</h3>
        <span className="spacer" />
        <span className="caption">{staged.length} configurado(s)</span>
      </div>

      {staged.length > 0 ? (
        <div className="table-wrap" style={{ marginBottom: 16 }}>
          <table className="dense">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Runner</th>
                <th>Repo</th>
                <th>Cenários</th>
                <th>Fila</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {staged.map((target) => (
                <tr key={target.name}>
                  <td className="mono">{target.name}</td>
                  <td>{target.kind}</td>
                  <td className="mono muted">{target.local_path}</td>
                  <td>{target.scenarios}</td>
                  <td>{target.queue_length}</td>
                  <td className="repo-actions">
                    <button className="btn-sm" onClick={() => void onScan(target.name)}>
                      Re-scan
                    </button>
                    <button className="btn-sm" onClick={() => editTarget(target)}>
                      Editar
                    </button>
                    <button className="btn-sm danger" onClick={() => removeTarget(target.name)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="muted" style={{ marginBottom: 16 }}>
          Nenhum target configurado ainda — preencha abaixo para adicionar um
          (sem precisar editar o arbites.yaml na mão).
        </p>
      )}

      <h4 className="section-title" style={{ marginTop: 0 }}>
        {editingName ? `Editando "${editingName}"` : "Adicionar target"}
      </h4>
      <div className="field-grid">
        <div className="field col-6">
          <label>Nome</label>
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="ex.: frontend-web"
          />
        </div>
        <div className="field col-6">
          <label>Timeout (minutos, opcional)</label>
          <input
            className="mono"
            value={timeoutText}
            onChange={(e) => setTimeoutText(e.target.value)}
            placeholder="30"
          />
        </div>
        <div className="field wide">
          <label>Caminho do repositório de automação</label>
          <div className="toolbar" style={{ margin: 0, gap: 6 }}>
            <input
              className="mono"
              style={{ flex: 1 }}
              value={form.local_path ?? ""}
              onChange={(e) => {
                setForm((f) => ({ ...f, local_path: e.target.value }));
                setFound(null);
              }}
              placeholder="C:/caminho/para/o/repo-de-automacao"
            />
            <button
              type="button"
              onClick={() => void browse()}
              disabled={!form.local_path?.trim() || browsing}
            >
              {browsing ? "Buscando…" : "Buscar arquivos .feature"}
            </button>
          </div>
        </div>
        <div className="field wide">
          <label>Padrão de arquivos .feature (avançado)</label>
          <input
            className="mono"
            value={form.features_glob ?? ""}
            onChange={(e) => {
              setForm((f) => ({ ...f, features_glob: e.target.value }));
              setFound(null);
            }}
          />
          <span className="caption muted">
            Deixe como está para incluir todos os cenários; use "Buscar" abaixo
            para restringir a um arquivo específico.
          </span>
        </div>
        <div className="field">
          <label>Python (venv, opcional)</label>
          <input
            className="mono"
            value={form.python_path ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, python_path: e.target.value }))}
            placeholder="C:/repo/.venv/Scripts/python.exe"
          />
        </div>
        <div className="field">
          <label>Diretório de trabalho (opcional)</label>
          <input
            className="mono"
            value={form.working_dir ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, working_dir: e.target.value }))}
            placeholder="vazio = usa o caminho do repositório"
          />
        </div>
      </div>

      {browseError && (
        <p className="caption" style={{ color: "var(--danger)" }}>
          {browseError}
        </p>
      )}

      {found && (
        <div className="modal-field">
          <label>
            {found.length === 0
              ? "Nenhum arquivo .feature encontrado com esse padrão."
              : `${found.length} arquivo(s) .feature encontrado(s):`}
          </label>
          {found.map((f) => (
            <div key={f.path} className="step-row">
              <span className="mono" style={{ flex: 1 }}>
                {f.path}
              </span>
              <span className="muted caption">
                {f.parseable ? `${f.scenarios} cenário(s)` : "não parseável"}
              </span>
              <button
                className="btn-sm"
                onClick={() => setForm((old) => ({ ...old, features_glob: f.path }))}
              >
                Usar só este
              </button>
            </div>
          ))}
          {found.length > 0 && (
            <button
              className="btn-sm"
              onClick={() => setForm((old) => ({ ...old, features_glob: DEFAULT_GLOB }))}
            >
              Usar todos (padrão)
            </button>
          )}
        </div>
      )}

      <div className="toolbar">
        <button
          onClick={stageTarget}
          disabled={!form.name.trim() || !form.local_path?.trim()}
        >
          {editingName ? "Atualizar na lista" : "Adicionar à lista"}
        </button>
        {editingName && <button onClick={resetForm}>Cancelar edição</button>}
        <span className="spacer" />
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Salvando…" : "Salvar configuração"}
        </button>
      </div>
    </div>
  );
}

function CIPanel({
  targets,
  onChanged,
  onError,
}: {
  targets: Target[];
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [tokenConfigured, setTokenConfigured] = useState<boolean | null>(null);
  const [tokenInput, setTokenInput] = useState("");
  const [target, setTarget] = useState("");
  const [tags, setTags] = useState("");
  const [ciFeature, setCiFeature] = useState("");
  const [ciEnv, setCiEnv] = useState("dev");
  const [ciBrowser, setCiBrowser] = useState("chrome");
  const [ciRepo, setCiRepo] = useState("");
  const [execId, setExecId] = useState<string | null>(null);
  const [status, setStatus] = useState<CIStatus | null>(null);
  const [collected, setCollected] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    json<{ configured: boolean }>(`${BASE}/settings/github/token`)
      .then((data) => setTokenConfigured(data.configured))
      .catch(() => setTokenConfigured(null));
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    setTarget((old) => old || targets[0]?.name || "");
  }, [targets]);

  async function saveToken() {
    try {
      const data = await json<{ configured: boolean }>(
        `${BASE}/settings/github/token`,
        { method: "PUT", body: JSON.stringify({ token: tokenInput }) },
      );
      setTokenConfigured(data.configured);
      setTokenInput("");
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function pollStatus(id: string) {
    if (timerRef.current) window.clearInterval(timerRef.current);
    const tick = () => {
      json<CIStatus>(`${BASE}/runs/ci/${id}/status`)
        .then((data) => {
          setStatus(data);
          if (data.workflow.status === "completed" && timerRef.current) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
          }
        })
        .catch((e) => onError(e.message));
    };
    tick();
    timerRef.current = window.setInterval(tick, 10000);
  }

  async function dispatch() {
    const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean);
    try {
      const execution = await json<{ id: string }>(`${BASE}/runs/ci`, {
        method: "POST",
        body: JSON.stringify({
          target,
          tags: tagList,
          feature: ciFeature || null,
          environment: ciEnv || null,
          browser: ciBrowser || null,
          source_repo: ciRepo || null,
        }),
      });
      setExecId(execution.id);
      setCollected(null);
      onChanged();
      pollStatus(execution.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function collect() {
    if (!execId) return;
    try {
      const data = await json<{ results_collected: number }>(
        `${BASE}/runs/ci/${execId}/collect`,
        { method: "POST" },
      );
      setCollected(`${data.results_collected} resultado(s) coletado(s).`);
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const dotFor = (s: string, c: string | null) =>
    s === "completed"
      ? c === "success"
        ? "dot-col-passed"
        : "dot-col-failed"
      : s === "in_progress"
        ? "dot-col-in_progress"
        : "dot-col-pending";

  return (
    <div className="card">
      <div className="card-head">
        <h3>GitHub Actions</h3>
        <span className="spacer" />
        <span className={`status-dot ${tokenConfigured ? "dot-col-passed" : "dot-col-pending"}`}>
          {tokenConfigured === null
            ? "status desconhecido"
            : tokenConfigured
              ? "PAT configurado"
              : "PAT não configurado"}
        </span>
      </div>

      <h4 className="section-title" style={{ marginTop: 0 }}>Token (keyring do sistema)</h4>
      <div className="step-row">
        <input
          type="password"
          placeholder="PAT fine-grained (actions: read+write no repo)"
          value={tokenInput}
          onChange={(e) => setTokenInput(e.target.value)}
        />
        <button onClick={() => void saveToken()} disabled={!tokenInput}>
          Salvar no keyring
        </button>
      </div>

      <h4 className="section-title">Disparar workflow</h4>
      <div className="field-grid">
        <div className="field col-3">
          <label>Target</label>
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {targets.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field col-3">
          <label>Arquivo .feature (opcional)</label>
          <input
            className="mono"
            placeholder="features/login.feature"
            value={ciFeature}
            onChange={(e) => setCiFeature(e.target.value)}
          />
        </div>
        <div className="field col-3">
          <label>Tag do Behave</label>
          <input
            placeholder="@regressao, @smoke"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
        </div>
        <div className="field col-3">
          <label>Ambiente</label>
          <select value={ciEnv} onChange={(e) => setCiEnv(e.target.value)}>
            <option value="dev">dev</option>
            <option value="cer">cer</option>
            <option value="prd">prd</option>
          </select>
        </div>
        <div className="field col-3">
          <label>Navegador</label>
          <select value={ciBrowser} onChange={(e) => setCiBrowser(e.target.value)}>
            <option value="chrome">chrome</option>
            <option value="edge">edge</option>
            <option value="firefox">firefox</option>
          </select>
        </div>
        <div className="field col-6">
          <label>Repositório de origem (opcional)</label>
          <input
            className="mono"
            placeholder="org/repositorio-que-disparou"
            value={ciRepo}
            onChange={(e) => setCiRepo(e.target.value)}
          />
        </div>
        <div className="field col-3" style={{ justifyContent: "flex-end" }}>
          <label>&nbsp;</label>
          <button className="primary" onClick={() => void dispatch()} disabled={!target}>
            workflow_dispatch
          </button>
        </div>
      </div>

      {status && (
        <>
          <h4 className="section-title">
            {status.execution_id} — workflow{" "}
            <span className={`status-dot ${dotFor(status.workflow.status, status.workflow.conclusion)}`}>
              {status.workflow.status}
              {status.workflow.conclusion ? ` (${status.workflow.conclusion})` : ""}
            </span>{" "}
            <a
              href={status.workflow.html_url}
              target="_blank"
              rel="noreferrer"
              style={{ color: "#2f81f7" }}
            >
              abrir no GitHub
            </a>
          </h4>
          {status.jobs.map((job) => (
            <div key={job.name} style={{ marginBottom: 8 }}>
              <div className="mono muted">{job.name}</div>
              {job.steps.map((step) => (
                <div key={step.name} className="step-row">
                  <span className={`status-dot ${dotFor(step.status, step.conclusion)}`}>
                    {step.name}
                  </span>
                  <span className="muted">
                    {step.status}
                    {step.conclusion ? ` · ${step.conclusion}` : ""}
                  </span>
                </div>
              ))}
            </div>
          ))}
          {status.workflow.status === "completed" && (
            <button className="primary" onClick={() => void collect()}>
              Coletar artifact (Cucumber JSON)
            </button>
          )}
          {collected && <p className="muted">{collected}</p>}
        </>
      )}
    </div>
  );
}

// ------------------------------------------------- artefatos (doc §1.5.1)

interface ArtifactFile {
  path: string;
  size: number;
  mtime: string;
}

function ArtifactsCard({ target, refreshKey }: { target: string; refreshKey: string }) {
  const [artifacts, setArtifacts] = useState<Record<string, ArtifactFile[]>>({});

  useEffect(() => {
    json<Record<string, ArtifactFile[]>>(`${BASE}/targets/${target}/artifacts`)
      .then(setArtifacts)
      .catch(() => setArtifacts({}));
  }, [target, refreshKey]);

  const kinds: { key: string; label: string }[] = [
    { key: "logs", label: "Logs (./logs)" },
    { key: "screenshots", label: "Screenshots (./screenshots)" },
    { key: "analise", label: "Análise de IA (./analise)" },
  ];
  const total = Object.values(artifacts).reduce((a, files) => a + files.length, 0);

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Artefatos pós-execução</h3>
        <span className="spacer" />
        <span className="caption">{total} arquivo(s)</span>
      </div>
      {total === 0 ? (
        <p className="muted">
          Nenhum artefato ainda — rode a automação e os arquivos de ./logs,
          ./screenshots e ./analise aparecem aqui.
        </p>
      ) : (
        kinds.map((k) =>
          (artifacts[k.key] ?? []).length === 0 ? null : (
            <div key={k.key} style={{ marginBottom: 12 }}>
              <h4 className="section-title" style={{ marginTop: 0 }}>{k.label}</h4>
              {(artifacts[k.key] ?? []).map((f) => (
                <div key={f.path} className="step-row">
                  <a
                    className="mono"
                    href={`${BASE}/targets/${target}/artifacts/file?kind=${k.key}&path=${encodeURIComponent(f.path)}`}
                    download
                  >
                    {f.path}
                  </a>
                  <span className="caption muted">
                    {(f.size / 1024).toFixed(1)} KB · {f.mtime}
                  </span>
                </div>
              ))}
            </div>
          ),
        )
      )}
    </div>
  );
}

// --------------------------------------------- .env visual (doc §1.5.1 e5)

interface CatalogEntry {
  section: string;
  key: string;
  description: string;
}

function EnvCard({ target, onError }: { target: string; onError: (m: string) => void }) {
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [dirty, setDirty] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    Promise.all([
      json<{ catalog: CatalogEntry[] }>(`${BASE}/env/catalog`),
      json<{ values: Record<string, string> }>(`${BASE}/targets/${target}/env`),
    ])
      .then(([c, e]) => {
        setCatalog(c.catalog);
        setValues(e.values);
        setDirty({});
      })
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [open, target, onError]);

  async function save() {
    setSaving(true);
    try {
      await json(`${BASE}/targets/${target}/env`, {
        method: "PUT",
        body: JSON.stringify({ values: dirty }),
      });
      setValues((old) => ({ ...old, ...dirty }));
      setDirty({});
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  const sections = [...new Set(catalog.map((c) => c.section))];
  const dirtyCount = Object.keys(dirty).length;

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-head">
        <h3>Configuração local (.env)</h3>
        <span className="spacer" />
        <button className="btn-sm" onClick={() => setOpen(!open)}>
          {open ? "Recolher" : "Editar variáveis"}
        </button>
      </div>
      {open && (
        <>
          {sections.map((section) => (
            <div key={section}>
              <h4 className="section-title">{section}</h4>
              <div className="field-grid">
                {catalog
                  .filter((c) => c.section === section)
                  .map((entry) => (
                    <div key={entry.key} className="field col-6">
                      <label title={entry.description}>{entry.key}</label>
                      <input
                        className="mono"
                        placeholder={entry.description}
                        value={dirty[entry.key] ?? values[entry.key] ?? ""}
                        onChange={(e) =>
                          setDirty((old) => ({ ...old, [entry.key]: e.target.value }))
                        }
                      />
                      <span className="caption muted">{entry.description}</span>
                    </div>
                  ))}
              </div>
            </div>
          ))}
          <div className="toolbar">
            <button
              className="primary"
              onClick={() => void save()}
              disabled={saving || dirtyCount === 0}
            >
              {saving ? "Salvando…" : `Salvar .env (${dirtyCount} alteração(ões))`}
            </button>
            <span className="caption muted">
              comentários e variáveis desconhecidas do .env são preservados
            </span>
          </div>
        </>
      )}
    </div>
  );
}
