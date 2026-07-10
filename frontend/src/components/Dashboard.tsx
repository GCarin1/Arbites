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
  AutomationReport,
  DefectsReport,
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
  const [defects, setDefects] = useState<DefectsReport | null>(null);
  const [automation, setAutomation] = useState<AutomationReport | null>(null);
  const [autoEnv, setAutoEnv] = useState("");

  useEffect(() => {
    api
      .squads()
      .then((r) => setSquads(r.squads))
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    try {
      const [s, t, f, m, d] = await Promise.all([
        api.metricsSummary(sprint, days, squad),
        api.metricsTrend(days === 15 ? 15 : days === 7 ? 7 : 30, sprint, squad),
        api.metricsFlaky(5),
        api.traceability("", sprint, squad),
        api.metricsDefects(squad),
      ]);
      setSummary(s);
      setTrend(t);
      setFlaky(f);
      setMatrix(m);
      setDefects(d);
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  }, [sprint, days, squad, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  // Automação tem filtro próprio de ambiente — recarrega só essa seção.
  useEffect(() => {
    api
      .metricsAutomation(days, autoEnv)
      .then(setAutomation)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [days, autoEnv, onError]);

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

      <div className="section-head">
        <h3 className="section-title" style={{ margin: 0 }}>
          Automação por repositório ({days} dias)
        </h3>
        <span className="spacer" style={{ flex: 1 }} />
        {automation && automation.envs.length > 0 && (
          <select value={autoEnv} onChange={(e) => setAutoEnv(e.target.value)}>
            <option value="">Todos os ambientes</option>
            {automation.envs.map((env) => (
              <option key={env} value={env}>
                {env}
              </option>
            ))}
          </select>
        )}
      </div>
      <AutomationPanel report={automation} />

      <h3 className="section-title">Defeitos abertos</h3>
      <DefectsPanel report={defects} />

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

const SEV_DOT: Record<string, string> = {
  critical: "dot-col-failed",
  high: "dot-col-failed",
  medium: "dot-col-blocked",
  low: "dot-col-pending",
};

const OUTCOME_DOT: Record<string, string> = {
  passed: "dot-col-passed",
  failed: "dot-col-failed",
  blocked: "dot-col-blocked",
  partial: "dot-col-in_progress",
  no_results: "dot-col-pending",
};

function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function mttrLabel(hours: number | null): string {
  if (hours === null) return "—";
  if (hours < 1) return `${Math.round(hours * 60)}min`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${Math.round(hours / 24)}d`;
}

function sinceLabel(iso: string | null): string | null {
  if (!iso) return null;
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (Number.isNaN(days)) return null;
  return days === 0 ? "hoje" : `${days}d`;
}

/** Sparkline dos runs recentes: um quadradinho por run, colorido pelo desfecho. */
function RunSparkline({ runs }: { runs: { at: string; outcome: string }[] }) {
  if (runs.length === 0) return <span className="muted">—</span>;
  return (
    <span className="run-spark">
      {runs.map((r, i) => (
        <span
          key={i}
          className={`run-cell run-${r.outcome}`}
          title={`${r.outcome} · ${r.at.slice(0, 10)}`}
        />
      ))}
    </span>
  );
}

function AutomationPanel({ report }: { report: AutomationReport | null }) {
  if (!report) return null;

  // Nada parseou: ou não há runs de automação, ou o padrão de nome precisa
  // de ajuste. Explica como configurar (genérico, sem citar empresa/projeto).
  if (report.by_repo.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-title">
          {report.unparsed > 0
            ? "Runs de automação não reconhecidos"
            : "Sem execuções de automação no período"}
        </div>
        <div className="empty-body">
          {report.unparsed > 0 ? (
            <>
              {report.unparsed} execução(ões) de automação não casaram o padrão
              de nome. Configure <span className="mono">ci_monitoring.name_pattern</span>{" "}
              no <span className="mono">arbites.yaml</span> (regex com os grupos{" "}
              <span className="mono">repo</span> e <span className="mono">env</span>)
              para extrair o repositório do nome da execução.
              {report.pattern_error && (
                <>
                  {" "}
                  <strong>Regex inválida:</strong> {report.pattern_error}
                </>
              )}
            </>
          ) : (
            <>
              Execuções vindas de GitHub Actions ou runs locais aparecem aqui,
              agrupadas pelo repositório (extraído do nome da execução).
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="chart-card">
      <div className="defects-summary">
        <div className="defect-stat">
          <div className="metric-value">{report.total_runs}</div>
          <div className="metric-label">runs</div>
        </div>
        <div className="defect-breakdown">
          <div className="defect-row">
            <span className="status-dot dot-col-passed">passaram: {report.passed_runs}</span>
            <span className="status-dot dot-col-failed">falharam: {report.failed_runs}</span>
            <span className="status-dot dot-col-in_progress">pass rate: {pct(report.pass_rate)}</span>
          </div>
          {report.unparsed > 0 && (
            <div className="defect-row caption">
              <span className="muted">
                {report.unparsed} run(s) fora do padrão de nome (não ranqueados)
              </span>
            </div>
          )}
        </div>
      </div>
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table className="dense">
          <thead>
            <tr>
              <th>Repositório</th>
              <th>Runs</th>
              <th>Falhas</th>
              <th>Taxa de falha</th>
              <th>Recentes</th>
              <th>MTTR</th>
              <th>Flaky</th>
              <th>Ambientes</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {report.by_repo.map((r) => {
              const broken = sinceLabel(r.broken_since);
              return (
                <tr key={r.repo}>
                  <td className="mono">{r.repo}</td>
                  <td>{r.runs}</td>
                  <td>{r.failed}</td>
                  <td>{pct(r.failure_rate)}</td>
                  <td>
                    <RunSparkline runs={r.recent} />
                  </td>
                  <td className="caption mono" title="tempo médio até voltar ao verde">
                    {mttrLabel(r.mttr_hours)}
                  </td>
                  <td>{r.flaky > 0 ? <span className="status-dot dot-col-blocked caption">{r.flaky}</span> : "—"}</td>
                  <td className="caption mono muted">{r.envs.join(", ") || "—"}</td>
                  <td>
                    {broken ? (
                      <span className="status-dot dot-col-failed caption" title="quebrado desde">
                        quebrado {broken}
                      </span>
                    ) : (
                      <span
                        className={`status-dot ${OUTCOME_DOT[r.last_outcome ?? ""] ?? "dot-col-pending"} caption`}
                      >
                        {r.last_outcome ?? "—"}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {report.top_failing_testcases.length > 0 && (
        <>
          <h4 className="section-title">Casos que mais falham (automação)</h4>
          <div className="table-wrap">
            <table className="dense">
              <thead>
                <tr>
                  <th>CT</th>
                  <th>Título</th>
                  <th>Falhas</th>
                  <th>Taxa de falha</th>
                  <th>Repositórios</th>
                </tr>
              </thead>
              <tbody>
                {report.top_failing_testcases.map((c) => (
                  <tr key={c.testcase_id}>
                    <td className="mono">{c.testcase_id}</td>
                    <td>{c.title ?? <span className="muted">— (CT ausente do índice)</span>}</td>
                    <td>
                      <span className="status-dot dot-col-failed caption">
                        {c.failed}/{c.runs}
                      </span>
                    </td>
                    <td>{pct(c.failure_rate)}</td>
                    <td className="caption mono muted">{c.repos.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {report.flaky_testcases.length > 0 && (
        <div className="defect-row caption" style={{ marginTop: 12 }}>
          <span className="status-dot dot-col-blocked">
            Flaky ({report.flaky_testcases.length})
          </span>
          <span className="mono muted">
            {report.flaky_testcases.map((f) => f.testcase_id).join(", ")}
          </span>
        </div>
      )}
    </div>
  );
}

function DefectsPanel({ report }: { report: DefectsReport | null }) {
  if (!report) return null;
  if (report.open_count === 0) {
    return (
      <div className="empty-state">
        <div className="empty-title">Nenhum defeito aberto</div>
        <div className="empty-body">
          Defeitos criados a partir de resultados failed aparecem aqui, com
          aging por severidade e squad.
        </div>
      </div>
    );
  }
  const aging = report.aging_buckets;
  return (
    <div className="chart-card">
      <div className="defects-summary">
        <div className="defect-stat">
          <div className="metric-value">{report.open_count}</div>
          <div className="metric-label">abertos</div>
        </div>
        <div className="defect-breakdown">
          <div className="defect-row">
            {Object.entries(report.by_severity).map(([sev, n]) => (
              <span key={sev} className={`status-dot ${SEV_DOT[sev] ?? "dot-col-pending"}`}>
                {sev}: {n}
              </span>
            ))}
          </div>
          <div className="defect-row caption">
            <span>Aging:</span>
            <span className="status-dot dot-col-passed">0–7d: {aging["0-7"]}</span>
            <span className="status-dot dot-col-blocked">8–30d: {aging["8-30"]}</span>
            <span className="status-dot dot-col-failed">30+d: {aging["30+"]}</span>
          </div>
        </div>
      </div>
      <div className="table-wrap" style={{ marginTop: 16 }}>
        <table className="dense">
          <thead>
            <tr>
              <th>ID</th>
              <th>Título</th>
              <th>Severidade</th>
              <th>Squad</th>
              <th>Idade</th>
              <th>CT</th>
              <th>Externo</th>
            </tr>
          </thead>
          <tbody>
            {report.items.map((d) => (
              <tr key={d.id}>
                <td className="mono">{d.id}</td>
                <td>{d.title}</td>
                <td>
                  <span className={`status-dot ${SEV_DOT[d.severity ?? ""] ?? "dot-col-pending"}`}>
                    {d.severity ?? "—"}
                  </span>
                </td>
                <td>{d.squad}</td>
                <td className="mono">{d.age_days === null ? "—" : `${d.age_days}d`}</td>
                <td className="mono muted">{d.testcase_id ?? "—"}</td>
                <td className="mono muted">{d.external_key ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
