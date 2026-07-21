import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { MentionTextarea, SingleRefInput } from "./Autocomplete";
import { ConfirmModal, Modal } from "./Modal";
import { useToast } from "./Toast";
import type {
  Execution,
  ExecutionDiff,
  ExecutionSummary,
  ResultEntry,
  TestCase,
} from "../types";

/**
 * Barra de progresso por PASSO: um segmento por step, colorido pelo status
 * (passed=verde, failed=vermelho, blocked=laranja, pending=trilho). "Enche" até
 * onde a execução chegou e mistura as cores na mesma linha.
 */
function StepBar({ steps }: { steps: ResultEntry["steps"] }) {
  if (steps.length === 0) return null;
  const marked = steps.filter((s) => s.status !== "pending").length;
  return (
    <div
      className="kanban-card-progress"
      title={`${marked}/${steps.length} passos executados`}
    >
      <div className="stepbar">
        {steps.map((s) => (
          <span key={s.index} className={`stepbar-seg seg-${s.status}`} />
        ))}
      </div>
      <span className="caption mono muted">
        {marked}/{steps.length}
      </span>
    </div>
  );
}

// ordem visual das colunas na barra empilhada da execução (concluídas primeiro).
const STACK_ORDER = ["passed", "retest", "failed", "blocked", "in_progress", "pending"];

/**
 * Barra empilhada da execução: um segmento por status, largura proporcional à
 * contagem, cada um na cor da sua coluna — não considera só os `passed`.
 */
function ExecStackBar({ results }: { results: ResultEntry[] }) {
  const counts: Record<string, number> = {};
  for (const r of results) {
    const key = r.column || r.status;
    counts[key] = (counts[key] ?? 0) + 1;
  }
  const total = results.length;
  return (
    <div className="exec-progress-bar exec-stack">
      {STACK_ORDER.map((key) =>
        counts[key] ? (
          <span
            key={key}
            className={`exec-seg col-${key}`}
            style={{ flexGrow: counts[key] }}
            title={`${key}: ${counts[key]}`}
          />
        ) : null,
      )}
      {total === 0 && <span className="exec-seg col-pending" style={{ flexGrow: 1 }} />}
    </div>
  );
}

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
      <div className="list-toolbar">
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

/**
 * Repositório de execuções centralizado (doc §1.3) — agrupado por ano de
 * criação (a "pasta" natural da execution), com expandir/colapsar e data.
 * Detalhe (board) abre só por clique.
 */
export function ExecutionsRepo({
  version,
  onOpen,
  onNew,
  onError,
  onNavigate,
}: {
  version: number;
  onOpen: (id: string) => void;
  onNew: () => void;
  onError: (message: string) => void;
  onNavigate?: (id: string) => void;
}) {
  const [items, setItems] = useState<ExecutionSummary[]>([]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<ExecutionSummary | null>(null);
  // modo Comparar: selecionar exatamente 2 executions → diff por categoria.
  const [compareMode, setCompareMode] = useState(false);
  const [picked, setPicked] = useState<string[]>([]);
  const [diff, setDiff] = useState<ExecutionDiff | null>(null);
  const { toast } = useToast();

  function toggleCompare() {
    setCompareMode((on) => !on);
    setPicked([]);
    setDiff(null);
  }

  function togglePick(id: string) {
    setPicked((old) => {
      if (old.includes(id)) return old.filter((x) => x !== id);
      if (old.length >= 2) return [old[1], id]; // mantém só os 2 últimos
      return [...old, id];
    });
  }

  async function runDiff() {
    if (picked.length !== 2) return;
    try {
      setDiff(await api.executionsDiff(picked[0], picked[1]));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  const load = useCallback(() => {
    api
      .executions()
      .then(setItems)
      .catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    load();
  }, [version, load]);

  async function remove(item: ExecutionSummary) {
    setDeleting(null);
    try {
      await api.deleteExecution(item.id);
      toast("Execução movida para a lixeira");
      load();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  function toggle(year: string) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (next.has(year)) next.delete(year);
      else next.add(year);
      return next;
    });
  }

  const byYear = new Map<string, ExecutionSummary[]>();
  for (const item of items) {
    const year = (item.created_at ?? "").slice(0, 4) || "sem data";
    byYear.set(year, [...(byYear.get(year) ?? []), item]);
  }
  const years = [...byYear.keys()].sort().reverse();

  return (
    <div className="repo">
      <div className="page-head">
        <h1 className="page-title">Execuções</h1>
        <span className="spacer" />
        <div className="head-controls">
          <button
            className={compareMode ? "primary" : ""}
            onClick={toggleCompare}
            disabled={items.length < 2}
            title="Selecionar duas execuções para comparar os resultados"
          >
            {compareMode ? "Cancelar comparação" : "Comparar"}
          </button>
          <button className="primary" onClick={onNew}>
            Nova execução
          </button>
        </div>
      </div>
      {compareMode && (
        <div className="card compare-bar">
          <span className="caption">
            Selecione duas execuções ({picked.length}/2)
            {picked.length > 0 && (
              <span className="mono muted"> — {picked.join(" ↔ ")}</span>
            )}
          </span>
          <span className="spacer" />
          <button
            className="primary"
            disabled={picked.length !== 2}
            onClick={() => void runDiff()}
          >
            Comparar selecionadas
          </button>
        </div>
      )}

      <div className="repo-tree card">
        {items.length === 0 ? (
          <div className="empty-state" style={{ border: "none" }}>
            <div className="empty-title">Nenhuma execução</div>
            <div className="empty-body">
              Crie uma execução para registrar resultados no kanban.
            </div>
          </div>
        ) : (
          years.map((year, yi) => {
            const isCollapsed = collapsed.has(year);
            const list = byYear.get(year) ?? [];
            const yearLast = yi === years.length - 1;
            const childPrefix = yearLast ? "    " : "│   ";
            return (
              <div key={year} className="repo-dir">
                <div className="repo-row repo-folder">
                  <span className="tree-prefix">{yearLast ? "└── " : "├── "}</span>
                  <button className="expand-btn" onClick={() => toggle(year)}>
                    {isCollapsed ? "▸" : "▾"}
                  </button>
                  <span className="repo-folder-name" onClick={() => toggle(year)}>
                    📁 {year}/
                  </span>
                  <span className="caption muted">{list.length}</span>
                </div>
                {!isCollapsed &&
                  list.map((item, ii) => {
                    const total = Object.values(item.result_counts).reduce(
                      (a, b) => a + b,
                      0,
                    );
                    const passed = item.result_counts["passed"] ?? 0;
                    return (
                      <div
                        key={item.id}
                        className={
                          "repo-row repo-file" +
                          (compareMode && picked.includes(item.id) ? " selected" : "")
                        }
                      >
                        <span className="tree-prefix">
                          {childPrefix + (ii === list.length - 1 ? "└── " : "├── ")}
                        </span>
                        <button
                          className="repo-file-main"
                          onClick={() =>
                            compareMode ? togglePick(item.id) : onOpen(item.id)
                          }
                        >
                          {compareMode && (
                            <span className="mono">
                              {picked.includes(item.id) ? "☑" : "☐"}
                            </span>
                          )}
                          <span className="mono muted">{item.id}</span>
                          <span className="repo-file-title">{item.name}</span>
                        </button>
                        <span className="caption mono muted">
                          {passed}/{total}
                        </span>
                        <span
                          className={`status-dot dot-${item.status === "closed" ? "done" : "active"} caption`}
                        >
                          {item.status}
                        </span>
                        <span className="caption mono muted">
                          {(item.created_at ?? "").slice(0, 10)}
                        </span>
                        <span className="repo-actions">
                          <button
                            className="btn-sm danger"
                            onClick={() => setDeleting(item)}
                          >
                            Excluir
                          </button>
                        </span>
                      </div>
                    );
                  })}
              </div>
            );
          })
        )}
      </div>
      {deleting && (
        <ConfirmModal
          title="Excluir execução"
          message={
            <>
              Mover <span className="mono">{deleting.id}</span> ({deleting.name})
              e suas evidências para a lixeira?
            </>
          }
          confirmLabel="Mover para a lixeira"
          danger
          onConfirm={() => void remove(deleting)}
          onCancel={() => setDeleting(null)}
        />
      )}
      {diff && (
        <Modal title={`Diff ${diff.a} → ${diff.b}`} onClose={() => setDiff(null)}>
          <ExecutionDiffView
            diff={diff}
            onNavigate={(id) => {
              setDiff(null);
              onNavigate?.(id);
            }}
          />
        </Modal>
      )}
    </div>
  );
}

// Painel de diff: uma seção por categoria, cada CT navegável.
const DIFF_SECTIONS: { key: keyof ExecutionDiff["categories"]; label: string }[] = [
  { key: "regressed", label: "Regrediram" },
  { key: "fixed", label: "Consertaram" },
  { key: "added", label: "Adicionados" },
  { key: "removed", label: "Removidos" },
  { key: "unchanged", label: "Sem mudança" },
];

function ExecutionDiffView({
  diff,
  onNavigate,
}: {
  diff: ExecutionDiff;
  onNavigate: (id: string) => void;
}) {
  const empty = DIFF_SECTIONS.every((s) => diff.counts[s.key] === 0);
  if (empty) {
    return <p className="empty">Nenhum CT em comum ou distinto entre as execuções.</p>;
  }
  return (
    <div className="exec-diff">
      {DIFF_SECTIONS.map((section) => {
        const entries = diff.categories[section.key];
        if (entries.length === 0) return null;
        return (
          <section key={section.key} className={`diff-cat diff-${section.key}`}>
            <h3 className="diff-cat-title">
              {section.label}{" "}
              <span className="caption mono muted">{entries.length}</span>
            </h3>
            <ul className="diff-list">
              {entries.map((e) => (
                <li key={e.testcase_id} className="diff-row">
                  <button
                    className="linklike mono"
                    onClick={() => onNavigate(e.testcase_id)}
                  >
                    {e.testcase_id}
                  </button>
                  <span className="diff-title">{e.title ?? "—"}</span>
                  <span className="caption mono muted">
                    {e.status_a ?? "∅"} → {e.status_b ?? "∅"}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
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
  const [squad, setSquad] = useState("");
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
        squad: squad || null,
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
        <div className="field">
          <label>Squad (opcional)</label>
          <input value={squad} onChange={(e) => setSquad(e.target.value)} />
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
  const [confirmClose, setConfirmClose] = useState(false);
  const [squadFilter, setSquadFilter] = useState("");
  const [squadOf, setSquadOf] = useState<Record<string, string | null>>({});
  const [titleOf, setTitleOf] = useState<Record<string, string>>({});
  // análise de falha pela IA (0096)
  const [analysis, setAnalysis] = useState<
    | null
    | "busy"
    | {
        summary: string;
        probable_cause: string;
        defect: { title: string; severity: string; description: string; testcase: string; execution: string };
      }
  >(null);
  const { toast } = useToast();

  const reload = useCallback(() => {
    api
      .execution(id)
      .then(setExecution)
      .catch((e) => onError(e.message));
  }, [id, onError]);

  useEffect(() => {
    setSelectedCt(null);
    setSquadFilter("");
    reload();
  }, [reload]);

  useEffect(() => {
    // mapa CT → squad efetivo (filtro do board) e título (exibição no card)
    api
      .testcases()
      .then((tcs) => {
        setSquadOf(Object.fromEntries(tcs.map((t) => [t.id, t.squad_effective])));
        setTitleOf(Object.fromEntries(tcs.map((t) => [t.id, t.title])));
      })
      .catch(() => {});
  }, []);

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

  async function analyzeRun() {
    setAnalysis("busy");
    try {
      setAnalysis(await api.aiAnalyzeRun(id));
    } catch (e) {
      setAnalysis(null);
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function createDefectFromDraft() {
    if (!analysis || analysis === "busy") return;
    try {
      await api.createDefect({
        title: analysis.defect.title,
        severity: analysis.defect.severity,
        testcase: analysis.defect.testcase,
        execution: analysis.defect.execution,
        body: analysis.defect.description,
      });
      toast("Defeito criado a partir da análise", "success");
      setAnalysis(null);
      onChanged();
      reload();
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function closeExecution() {
    setConfirmClose(false);
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

  const squadsInExec = [
    ...new Set(
      execution.results.map((r) => squadOf[r.testcase_id]).filter((s): s is string => !!s),
    ),
  ].sort();
  const visible = squadFilter
    ? execution.results.filter((r) => squadOf[r.testcase_id] === squadFilter)
    : execution.results;

  const total = visible.length;
  const passed = visible.filter((r) => (r.column || r.status) === "passed").length;

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">
          <span className="mono muted">{execution.id}</span>
          <span>{execution.name}</span>
        </h1>
        <span className="spacer" />
        <div className="head-controls">
          <span className="caption">
            {execution.sprint ?? "—"} · {execution.environment ?? "—"}
          </span>
          {squadsInExec.length > 0 && (
            <select
              value={squadFilter}
              onChange={(e) => setSquadFilter(e.target.value)}
              aria-label="Filtrar por squad"
            >
              <option value="">Todas as squads</option>
              {squadsInExec.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
          <span className={`status-dot dot-${closed ? "done" : "active"}`}>
            {execution.status}
          </span>
          {execution.results.some((r) =>
            ["failed", "blocked"].includes(r.column || r.status),
          ) && (
            <button onClick={() => void analyzeRun()} disabled={analysis === "busy"}>
              {analysis === "busy" ? "Analisando…" : "Analisar falha (IA)"}
            </button>
          )}
          {!closed && (
            <button onClick={() => setConfirmClose(true)}>Fechar execução</button>
          )}
        </div>
      </div>

      {analysis && analysis !== "busy" && (
        <Modal
          title="Análise da falha (IA)"
          onClose={() => setAnalysis(null)}
          footer={
            <>
              <button onClick={() => setAnalysis(null)}>Descartar</button>
              <button className="primary" onClick={() => void createDefectFromDraft()}>
                Criar defeito
              </button>
            </>
          }
        >
          <p className="modal-text"><strong>Resumo:</strong> {analysis.summary}</p>
          {analysis.probable_cause && (
            <p className="modal-text"><strong>Causa provável:</strong> {analysis.probable_cause}</p>
          )}
          <div className="card block">
            <div className="card-head">
              <h4 className="section-title" style={{ margin: 0 }}>Rascunho de defeito</h4>
              <span className="spacer" />
              <span
                className={`status-dot ${
                  ["critical", "high"].includes(analysis.defect.severity)
                    ? "dot-col-failed"
                    : analysis.defect.severity === "medium"
                      ? "dot-col-blocked"
                      : "dot-col-pending"
                } caption`}
              >
                {analysis.defect.severity}
              </span>
            </div>
            <p className="modal-text"><strong>{analysis.defect.title}</strong></p>
            <p className="modal-text caption muted">{analysis.defect.description}</p>
            <p className="caption muted">
              vinculado a <span className="mono">{analysis.defect.testcase}</span> ·{" "}
              <span className="mono">{analysis.defect.execution}</span>
            </p>
          </div>
        </Modal>
      )}

      {confirmClose && (
        <ConfirmModal
          title="Fechar execução"
          message={
            <>
              Fechar <span className="mono">{id}</span>? Os resultados ficam{" "}
              <strong>imutáveis</strong> e a execução não poderá mais ser editada.
            </>
          }
          confirmLabel="Fechar execução"
          onConfirm={() => void closeExecution()}
          onCancel={() => setConfirmClose(false)}
        />
      )}

      <div className="exec-progress">
        <ExecStackBar results={visible} />
        <span className="caption mono">
          {passed}/{total} passed
        </span>
      </div>

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
              <span className="count">
                {visible.filter((r) => (r.column || r.status) === col.key).length}
              </span>
            </div>
            {visible
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
                  <div className="kanban-card-head">
                    <span className="mono">{result.testcase_id}</span>
                    {squadOf[result.testcase_id] && !squadFilter && (
                      <span className="muted"> · {squadOf[result.testcase_id]}</span>
                    )}
                  </div>
                  {titleOf[result.testcase_id] && (
                    <div className="kanban-card-title">{titleOf[result.testcase_id]}</div>
                  )}
                  <StepBar steps={result.steps} />
                  {(result.evidences.length > 0 || result.defects.length > 0) && (
                    <div className="kanban-card-meta caption muted">
                      {result.evidences.length > 0 && <span>{result.evidences.length} evid.</span>}
                      {result.defects.length > 0 && (
                        <span className="mono">{result.defects.join(", ")}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>

      {selectedResult && (
        <Modal
          title={`${selectedResult.testcase_id} · ${titleOf[selectedResult.testcase_id] ?? ""}`}
          onClose={() => setSelectedCt(null)}
        >
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
        </Modal>
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
  const [savingComment, setSavingComment] = useState(false);
  const [creatingDefect, setCreatingDefect] = useState(false);
  const [linkingDefect, setLinkingDefect] = useState(false);
  const [pickedDefect, setPickedDefect] = useState("");

  // Reseta só ao TROCAR de CT — nunca por `result.comment`, senão um refresh de
  // fundo (ou outra ação) reescreve o campo por baixo do que o usuário digitou.
  useEffect(() => {
    setComment(result.comment ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result.testcase_id]);

  const commentDirty = comment !== (result.comment ?? "");

  async function markStep(step: number, status: string) {
    try {
      onUpdate(await api.stepStatus(execution.id, result.testcase_id, step, status));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function saveComment() {
    setSavingComment(true);
    try {
      // preserva a coluna atual (status e coluna podem divergir); só grava o texto.
      onUpdate(
        await api.resultStatus(execution.id, result.testcase_id, {
          status: result.status,
          column: result.column || result.status,
          comment,
        }),
      );
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingComment(false);
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

  async function createDefect(title: string, external: string | null) {
    setCreatingDefect(false);
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

  async function linkExistingDefect() {
    if (!pickedDefect) return;
    try {
      onUpdate(await api.linkDefect(execution.id, result.testcase_id, pickedDefect));
      setLinkingDefect(false);
      setPickedDefect("");
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  async function unlinkDefect(defectId: string) {
    try {
      onUpdate(await api.unlinkDefect(execution.id, result.testcase_id, defectId));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="result-panel">
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
      {closed ? (
        <p className="muted">{comment || "—"}</p>
      ) : (
        <>
          <MentionTextarea
            value={comment}
            onChange={setComment}
            placeholder="Comentário — digite @ para referenciar um card (ex.: @DF-0007)"
          />
          <div className="toolbar">
            <button
              className="primary"
              onClick={() => void saveComment()}
              disabled={!commentDirty || savingComment}
            >
              {savingComment ? "Salvando…" : commentDirty ? "Salvar comentário" : "Salvo"}
            </button>
          </div>
        </>
      )}

      <h4>Defeitos</h4>
      {result.defects.length > 0 ? (
        result.defects.map((defectId) => (
          <div key={defectId} className="step-row">
            <span className="mono" style={{ flex: 1 }}>
              {defectId}
            </span>
            {!closed && (
              <button className="danger" onClick={() => void unlinkDefect(defectId)}>
                desvincular
              </button>
            )}
          </div>
        ))
      ) : (
        <p className="muted">Nenhum defeito vinculado.</p>
      )}
      {!closed && (
        <div className="toolbar">
          <button onClick={() => setCreatingDefect(true)}>
            Criar defeito a partir deste resultado
          </button>
          <button onClick={() => setLinkingDefect((v) => !v)}>
            Vincular defeito existente
          </button>
        </div>
      )}

      {linkingDefect && !closed && (
        <div className="step-row">
          <SingleRefInput
            value={pickedDefect}
            onChange={setPickedDefect}
            kinds="defect"
            placeholder="DF-0001 — digite id ou título do defeito"
            onEnterNoMatch={() => void linkExistingDefect()}
          />
          <button
            className="primary"
            disabled={!pickedDefect}
            onClick={() => void linkExistingDefect()}
          >
            Vincular
          </button>
          <button onClick={() => setLinkingDefect(false)}>Cancelar</button>
        </div>
      )}

      {creatingDefect && (
        <NewDefectModal
          testcaseId={result.testcase_id}
          onSubmit={createDefect}
          onClose={() => setCreatingDefect(false)}
        />
      )}
    </div>
  );
}

function NewDefectModal({
  testcaseId,
  onSubmit,
  onClose,
}: {
  testcaseId: string;
  onSubmit: (title: string, external: string | null) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [external, setExternal] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);

  function submit() {
    if (!title.trim()) return;
    onSubmit(title.trim(), external.trim() || null);
  }

  return (
    <Modal
      title="Criar defeito"
      onClose={onClose}
      initialFocus={titleRef}
      footer={
        <>
          <button onClick={onClose}>Cancelar</button>
          <button className="primary" onClick={submit} disabled={!title.trim()}>
            Criar defeito
          </button>
        </>
      }
    >
      <p className="modal-text muted">
        A partir de <span className="mono">{testcaseId}</span> · severidade{" "}
        <span className="mono">high</span>.
      </p>
      <form
        className="modal-field"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label htmlFor="new-defect-title">Título</label>
        <input
          id="new-defect-title"
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex.: Botão de login não responde"
        />
      </form>
      <div className="modal-field">
        <label htmlFor="new-defect-external">Chave externa (opcional)</label>
        <input
          id="new-defect-external"
          className="mono"
          value={external}
          onChange={(e) => setExternal(e.target.value)}
          placeholder="PROJ-123"
        />
      </div>
    </Modal>
  );
}
