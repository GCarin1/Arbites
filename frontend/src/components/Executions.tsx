import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Execution, ExecutionSummary, ResultEntry, TestCase } from "../types";

const COLUMNS: { key: string; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "in_progress", label: "In Progress" },
  { key: "blocked", label: "Blocked" },
  { key: "failed", label: "Failed" },
  { key: "retest", label: "Retest" },
  { key: "passed", label: "Passed" },
];

// ---------------------------------------------------------------- sidebar

export function ExecutionsList({
  version,
  selected,
  onSelect,
  onNew,
  onError,
}: {
  version: number;
  selected: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onError: (message: string) => void;
}) {
  const [items, setItems] = useState<ExecutionSummary[]>([]);

  useEffect(() => {
    api
      .executions()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [version, onError]);

  return (
    <div>
      <div style={{ padding: "0 0 8px" }}>
        <button className="primary" onClick={onNew}>
          Nova execução
        </button>
      </div>
      {items.map((item) => {
        const total = Object.values(item.result_counts).reduce((a, b) => a + b, 0);
        const passed = item.result_counts["passed"] ?? 0;
        return (
          <button
            key={item.id}
            className={`list-item ${item.id === selected ? "selected" : ""}`}
            onClick={() => onSelect(item.id)}
          >
            <span className="mono muted">{item.id}</span>
            <span style={{ flex: 1 }}>{item.name}</span>
            <span className="muted mono">
              {passed}/{total}
            </span>
            <span className={`status-dot dot-${item.status === "closed" ? "done" : "active"}`} />
          </button>
        );
      })}
      {items.length === 0 && <p className="muted">Nenhuma execução ainda.</p>}
    </div>
  );
}

// ---------------------------------------------------------------- criação

export function ExecutionCreate({
  onCreated,
  onError,
}: {
  onCreated: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [name, setName] = useState("");
  const [sprint, setSprint] = useState("");
  const [environment, setEnvironment] = useState("");
  const [available, setAvailable] = useState<TestCase[]>([]);
  const [chosen, setChosen] = useState<Set<string>>(new Set());

  useEffect(() => {
    api
      .testcases()
      .then(setAvailable)
      .catch((e) => onError(e.message));
  }, [onError]);

  function toggle(id: string) {
    setChosen((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function create() {
    if (!name || chosen.size === 0) {
      onError("Informe o nome e selecione ao menos um CT.");
      return;
    }
    try {
      const execution = await api.createExecution({
        name,
        sprint: sprint || null,
        environment: environment || null,
        testcase_ids: [...chosen],
      });
      onCreated(execution.id);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editor">
      <h2>Nova execução</h2>
      <div className="field-grid">
        <div className="field">
          <label>Nome</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label>Sprint (texto livre)</label>
          <input value={sprint} onChange={(e) => setSprint(e.target.value)} />
        </div>
        <div className="field">
          <label>Ambiente (texto livre)</label>
          <input value={environment} onChange={(e) => setEnvironment(e.target.value)} />
        </div>
      </div>
      <div className="field wide">
        <label>
          Test cases ({chosen.size} selecionado{chosen.size === 1 ? "" : "s"})
        </label>
        <div className="ct-picker">
          {available.map((tc) => (
            <label key={tc.id} className="ct-option">
              <input
                type="checkbox"
                checked={chosen.has(tc.id)}
                onChange={() => toggle(tc.id)}
              />
              <span className="mono muted">{tc.id}</span>
              <span style={{ flex: 1 }}>{tc.title}</span>
              <span className={`status-dot dot-${tc.status} muted`}>{tc.status}</span>
            </label>
          ))}
          {available.length === 0 && (
            <p className="muted" style={{ padding: 8 }}>
              Nenhum CT no workspace.
            </p>
          )}
        </div>
      </div>
      <div className="toolbar">
        <button className="primary" onClick={() => void create()}>
          Criar execução
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- board

export function ExecutionBoard({
  id,
  onChanged,
  onError,
}: {
  id: string;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [selectedCt, setSelectedCt] = useState<string | null>(null);
  const [dragCt, setDragCt] = useState<string | null>(null);

  const reload = useCallback(() => {
    api
      .execution(id)
      .then(setExecution)
      .catch((e) => onError(e.message));
  }, [id, onError]);

  useEffect(() => {
    setSelectedCt(null);
    reload();
  }, [reload]);

  if (!execution) return <p className="empty">Carregando {id}…</p>;

  const closed = execution.status === "closed";

  async function moveTo(ctId: string, status: string) {
    try {
      const updated = await api.resultStatus(id, ctId, { status });
      setExecution(updated);
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function closeExecution() {
    if (!window.confirm(`Fechar ${id}? Resultados ficam imutáveis.`)) return;
    try {
      const updated = await api.closeExecution(id);
      setExecution(updated);
      onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const selectedResult =
    execution.results.find((r) => r.testcase_id === selectedCt) ?? null;

  return (
    <div>
      <h2 style={{ fontSize: 16, display: "flex", gap: 12, alignItems: "baseline" }}>
        <span className="mono muted">{execution.id}</span>
        <span>{execution.name}</span>
        <span className="muted" style={{ fontSize: 12 }}>
          {execution.sprint ?? "—"} · {execution.environment ?? "—"} ·{" "}
          <span className={`status-dot dot-${closed ? "done" : "active"}`}>
            {execution.status}
          </span>
        </span>
        <span style={{ flex: 1 }} />
        {!closed && <button onClick={() => void closeExecution()}>Fechar execução</button>}
      </h2>

      <div className="kanban">
        {COLUMNS.map((col) => (
          <div
            key={col.key}
            className="kanban-col"
            onDragOver={(e) => {
              if (!closed) e.preventDefault();
            }}
            onDrop={() => {
              if (!closed && dragCt) void moveTo(dragCt, col.key);
              setDragCt(null);
            }}
          >
            <div className="kanban-col-title">
              <span className={`status-dot dot-col-${col.key}`}>{col.label}</span>
              <span className="muted mono">
                {execution.results.filter((r) => (r.column || r.status) === col.key).length}
              </span>
            </div>
            {execution.results
              .filter((r) => (r.column || r.status) === col.key)
              .map((result) => (
                <div
                  key={result.testcase_id}
                  className={`kanban-card ${
                    result.testcase_id === selectedCt ? "selected" : ""
                  }`}
                  draggable={!closed}
                  onDragStart={() => setDragCt(result.testcase_id)}
                  onClick={() => setSelectedCt(result.testcase_id)}
                >
                  <span className="mono">{result.testcase_id}</span>
                  {result.evidences.length > 0 && (
                    <span className="muted"> · {result.evidences.length} evid.</span>
                  )}
                  {result.defects.length > 0 && (
                    <span className="muted"> · {result.defects.join(", ")}</span>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>

      {selectedResult && (
        <ResultPanel
          execution={execution}
          result={selectedResult}
          closed={closed}
          onUpdate={(updated) => {
            setExecution(updated);
            onChanged();
          }}
          onError={onError}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------- painel

function ResultPanel({
  execution,
  result,
  closed,
  onUpdate,
  onError,
}: {
  execution: Execution;
  result: ResultEntry;
  closed: boolean;
  onUpdate: (execution: Execution) => void;
  onError: (message: string) => void;
}) {
  const [note, setNote] = useState("");
  const [comment, setComment] = useState(result.comment ?? "");

  useEffect(() => {
    setComment(result.comment ?? "");
  }, [result.testcase_id, result.comment]);

  async function markStep(step: number, status: string) {
    try {
      onUpdate(await api.stepStatus(execution.id, result.testcase_id, step, status));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function saveComment() {
    try {
      onUpdate(
        await api.resultStatus(execution.id, result.testcase_id, {
          status: result.status,
          comment,
        }),
      );
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function upload(files: FileList | null) {
    if (!files || files.length === 0) return;
    try {
      await api.uploadEvidence(execution.id, result.testcase_id, files[0], note);
      onUpdate(await api.execution(execution.id));
      setNote("");
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function removeEvidence(index: number) {
    try {
      onUpdate(await api.deleteEvidence(execution.id, result.testcase_id, index));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function createDefect() {
    const title = window.prompt("Título do defeito:");
    if (!title) return;
    const external = window.prompt("Chave externa (opcional, ex.: PROJ-123):") || null;
    try {
      await api.createDefect({
        title,
        severity: "high",
        testcase: result.testcase_id,
        execution: execution.id,
        external_key: external,
      });
      onUpdate(await api.execution(execution.id));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="result-panel">
      <h3 className="mono">{result.testcase_id}</h3>

      <h4>Passos</h4>
      {result.steps.length === 0 && <p className="muted">CT sem passos estruturados.</p>}
      {result.steps.map((step) => (
        <div key={step.index} className="step-row">
          <span className={`status-dot dot-step-${step.status} mono`}>{step.index}.</span>
          <span style={{ flex: 1 }}>{step.text}</span>
          {!closed && (
            <span className="step-actions">
              <button onClick={() => void markStep(step.index, "passed")}>pass</button>
              <button onClick={() => void markStep(step.index, "failed")}>fail</button>
              <button onClick={() => void markStep(step.index, "blocked")}>block</button>
            </span>
          )}
          <span className="muted">{step.status}</span>
        </div>
      ))}

      <h4>Evidências</h4>
      {result.evidences.map((evidence, i) => (
        <div key={i} className="step-row">
          <span className="mono" style={{ flex: 1 }}>
            {evidence.path}
          </span>
          <span className="muted mono" title={evidence.sha256}>
            {evidence.sha256.slice(0, 12)}…
          </span>
          {evidence.note && <span className="muted">{evidence.note}</span>}
          {!closed && (
            <button className="danger" onClick={() => void removeEvidence(i)}>
              remover
            </button>
          )}
        </div>
      ))}
      {!closed && (
        <div className="step-row">
          <input
            placeholder="nota da evidência (opcional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            style={{ maxWidth: 280 }}
          />
          <input type="file" onChange={(e) => void upload(e.target.files)} />
        </div>
      )}

      <h4>Comentário</h4>
      <div className="step-row">
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={closed}
        />
        {!closed && <button onClick={() => void saveComment()}>Salvar</button>}
      </div>

      <h4>Defeitos</h4>
      {result.defects.length > 0 ? (
        <p className="mono">{result.defects.join(", ")}</p>
      ) : (
        <p className="muted">Nenhum defeito vinculado.</p>
      )}
      {!closed && (
        <button onClick={() => void createDefect()}>
          Criar defeito a partir deste resultado
        </button>
      )}
    </div>
  );
}
