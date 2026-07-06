import { useCallback, useEffect, useRef, useState } from "react";

const BASE = "/api/v1";

interface Target {
  name: string;
  kind: string;
  local_path: string | null;
  features_glob: string | null;
  scenarios: number;
  queue_length: number;
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
          body: JSON.stringify({ target: selection, tags: tagList }),
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

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Automação</h1>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-head">
          <h3>Targets</h3>
          <span className="spacer" />
          <span className="caption">{targets.length} configurado(s)</span>
        </div>
        <div className="table-wrap">
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
              {targets.map((target) => (
                <tr key={target.name}>
                  <td className="mono">{target.name}</td>
                  <td>{target.kind}</td>
                  <td className="mono muted">{target.local_path}</td>
                  <td>{target.scenarios}</td>
                  <td>{target.queue_length}</td>
                  <td>
                    <button className="btn-sm" onClick={() => void scan(target.name)}>
                      Re-scan
                    </button>
                  </td>
                </tr>
              ))}
              {targets.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    Nenhum target configurado — adicione em arbites.yaml
                    (automation_targets).
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-head">
          <h3>Novo run local (Behave)</h3>
        </div>
        <div className="step-row">
          <select
            value={selection}
            onChange={(e) => setSelection(e.target.value)}
            style={{ maxWidth: 220, flex: "0 0 auto" }}
          >
            {targets.map((target) => (
              <option key={target.name} value={target.name}>
                {target.name}
              </option>
            ))}
          </select>
          <input
            placeholder="tags (ex.: @CT-0001, @smoke) — vazio não é permitido"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
          <button className="primary" onClick={() => void startRun()} disabled={!selection}>
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
        body: JSON.stringify({ target, tags: tagList }),
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
      <div className="step-row">
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          style={{ maxWidth: 220, flex: "0 0 auto" }}
        >
          {targets.map((t) => (
            <option key={t.name} value={t.name}>
              {t.name}
            </option>
          ))}
        </select>
        <input
          placeholder="tags (ex.: @CT-0001)"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />
        <button className="primary" onClick={() => void dispatch()} disabled={!target}>
          workflow_dispatch
        </button>
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
