import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import type {
  Execution,
  FlakyReport,
  MatrixStory,
  MetricValue,
  MetricsSummary,
  TraceabilityMatrix,
  TrendPoint,
} from "../types";

export function Dashboard({ onError }: { onError: (message: string) => void }) {
  const [sprint, setSprint] = useState("");
  const [days, setDays] = useState(30);
  const [squad, setSquad] = useState("");
  const [squads, setSquads] = useState<string[]>([]);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [flaky, setFlaky] = useState<FlakyReport | null>(null);
  const [matrix, setMatrix] = useState<TraceabilityMatrix | null>(null);

  useEffect(() => {
    api
      .squads()
      .then((r) => setSquads(r.squads))
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    try {
      const [s, t, f, m] = await Promise.all([
        api.metricsSummary(sprint, days, squad),
        api.metricsTrend(days === 15 ? 15 : days === 7 ? 7 : 30, sprint, squad),
        api.metricsFlaky(5),
        api.traceability("", sprint, squad),
      ]);
      setSummary(s);
      setTrend(t);
      setFlaky(f);
      setMatrix(m);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }, [sprint, days, squad, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div>
      <div className="page-head">
        <h1 className="page-title">Dashboard</h1>
        <span className="spacer" />
        <div className="head-controls">
          <input
            placeholder="filtrar por sprint"
            value={sprint}
            onChange={(e) => setSprint(e.target.value)}
          />
          {squads.length > 0 && (
            <select
              value={squad}
              onChange={(e) => setSquad(e.target.value)}
              aria-label="Filtrar por squad"
            >
              <option value="">Todas as squads</option>
              {squads.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>7 dias</option>
            <option value={15}>15 dias</option>
            <option value={30}>30 dias</option>
          </select>
          <a className="button-link" href={api.exportUrl("md", sprint, squad)} download>
            Export MD
          </a>
          <a className="button-link" href={api.exportUrl("pdf", sprint, squad)} download>
            Export PDF
          </a>
        </div>
      </div>

      {summary && (
        <div className="metric-cards">
          <MetricCard label="Cobertura de requisito" metric={summary.requirement_coverage} />
          <MetricCard label="Cobertura de execução" metric={summary.execution_coverage} />
          <MetricCard label="Pass rate" metric={summary.pass_rate} />
          <MetricCard label="Taxa de bloqueio" metric={summary.blocked_rate} />
          <MetricCard label="Retrabalho" metric={summary.rework_rate} />
          <div className="metric-card">
            <div className="metric-label">Instabilidade (flaky)</div>
            <div className="metric-value">{flaky?.testcases.length ?? 0}</div>
            <div className="metric-formula mono">
              {flaky?.testcases.map((f) => f.testcase_id).join(", ") || "nenhum CT"}
            </div>
          </div>
        </div>
      )}

      <h3 className="section-title">Tendência ({days} dias)</h3>
      <div className="chart-card" style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <BarChart data={trend} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
            <CartesianGrid stroke="#30363d" vertical={false} />
            <XAxis dataKey="day" stroke="#8b949e" fontSize={11} tickFormatter={(d: string) => d.slice(5)} />
            <YAxis stroke="#8b949e" fontSize={11} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#161b22", border: "1px solid #30363d" }}
              labelStyle={{ color: "#e6edf3" }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="passed" stackId="a" fill="#238636" name="passed" />
            <Bar dataKey="failed" stackId="a" fill="#da3633" name="failed" />
            <Bar dataKey="blocked" stackId="a" fill="#d29922" name="blocked" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h3 className="section-title">Matriz de rastreabilidade</h3>
      {matrix && matrix.epics.length === 0 && (
        <div className="empty-state">
          <div className="empty-title">Nenhum epic no workspace</div>
          <div className="empty-body">
            Crie epics e stories na aba Requisitos para ver a matriz de
            rastreabilidade até a evidência.
          </div>
        </div>
      )}
      {matrix?.epics.map((epic) => (
        <div key={epic.id} className="matrix-epic">
          <div className="matrix-epic-title">
            <span className="mono muted">{epic.id}</span> {epic.title}
          </div>
          <div className="table-wrap">
          <table className="dense">
            <thead>
              <tr>
                <th>Story</th>
                <th>CTs</th>
                <th>Último resultado</th>
                <th>Execution</th>
                <th>Evidências</th>
                <th>Defeitos</th>
              </tr>
            </thead>
            <tbody>
              {epic.stories.map((story) => (
                <StoryRow key={story.id} story={story} onError={onError} />
              ))}
            </tbody>
          </table>
          </div>
        </div>
      ))}
    </div>
  );
}

function MetricCard({ label, metric }: { label: string; metric: MetricValue }) {
  const pct = metric.value === null ? "—" : `${Math.round(metric.value * 100)}%`;
  const status = metric.status ?? "none";
  const goal =
    status !== "none" && metric.threshold?.warn !== undefined
      ? `meta ${metric.threshold.direction === "down" ? "≤" : "≥"} ${Math.round(
          (metric.threshold.warn ?? 0) * 100,
        )}%`
      : null;
  return (
    <div className={`metric-card metric-${status}`}>
      <div className="metric-label">
        {label}
        {status !== "none" && <span className={`metric-flag flag-${status}`} title={goal ?? ""} />}
      </div>
      <div className="metric-value">{pct}</div>
      <div className="metric-formula mono" title={metric.formula}>
        {goal ? `${goal} · ` : ""}
        {metric.numerator}/{metric.denominator}
      </div>
    </div>
  );
}

function StoryRow({
  story,
  onError,
}: {
  story: MatrixStory;
  onError: (message: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [evidenceOf, setEvidenceOf] = useState<Execution | null>(null);

  const statusLabel = story.last_status ?? (story.covered ? "sem execução" : "sem cobertura");
  const dotClass = story.last_status
    ? `dot-col-${story.last_status}`
    : story.covered
      ? "dot-col-pending"
      : "dot-col-pending";

  async function drill(executionId: string) {
    try {
      setEvidenceOf(await api.execution(executionId));
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <>
      <tr className="matrix-row" onClick={() => setOpen(!open)}>
        <td>
          <span className="mono muted">{story.id}</span> {story.title}
        </td>
        <td>{story.ct_count}</td>
        <td>
          <span className={`status-dot ${dotClass}`}>{statusLabel}</span>
        </td>
        <td className="mono">{story.last_execution ?? "—"}</td>
        <td>{story.evidence_count}</td>
        <td className="mono">
          {story.defects.map((d) => d.id).join(", ") || "—"}
        </td>
      </tr>
      {open &&
        story.testcases.map((tc) => (
          <tr key={tc.id} className="matrix-ct-row">
            <td style={{ paddingLeft: 24 }}>
              <span className="mono muted">{tc.id}</span> {tc.title}
            </td>
            <td />
            <td>
              {tc.last_result ? (
                <span className={`status-dot dot-col-${tc.last_result.status}`}>
                  {tc.last_result.status}
                </span>
              ) : (
                <span className="muted">nunca executado</span>
              )}
            </td>
            <td className="mono">
              {tc.last_result ? (
                <button
                  className="link-btn"
                  onClick={() => void drill(tc.last_result!.execution_id)}
                >
                  {tc.last_result.execution_id}
                </button>
              ) : (
                "—"
              )}
            </td>
            <td colSpan={2}>
              {evidenceOf &&
                tc.last_result &&
                evidenceOf.id === tc.last_result.execution_id &&
                (evidenceOf.results.find((r) => r.testcase_id === tc.id)?.evidences ?? [])
                  .map((evidence, i) => (
                    <a
                      key={i}
                      className="mono"
                      style={{ display: "block", color: "#2f81f7" }}
                      href={api.evidenceFileUrl(evidenceOf.id, tc.id, i)}
                      download
                    >
                      {evidence.path}
                    </a>
                  ))}
            </td>
          </tr>
        ))}
    </>
  );
}
