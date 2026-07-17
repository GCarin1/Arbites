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
  DashboardOverview,
  DefectsReport,
  Execution,
  FlakyReport,
  HealthScore,
  MatrixStory,
  MetricValue,
  MetricsSummary,
  RiskMap,
  RiskMapFile,
  TraceabilityMatrix,
  TrendPoint,
} from "../types";

export function Dashboard({
  onError,
  onNavigate,
}: {
  onError: (message: string) => void;
  onNavigate?: (id: string) => void;
}) {
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
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [riskMap, setRiskMap] = useState<RiskMap | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);

  useEffect(() => {
    api
      .squads()
      .then((r) => setSquads(r.squads))
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    try {
      const [s, t, f, m, d, h, o] = await Promise.all([
        api.metricsSummary(sprint, days, squad),
        api.metricsTrend(days === 15 ? 15 : days === 7 ? 7 : 30, sprint, squad),
        api.metricsFlaky(5),
        api.traceability("", sprint, squad),
        api.metricsDefects(squad),
        api.metricsHealth(sprint, days, squad),
        api.metricsDashboard(sprint, days, squad),
      ]);
      setSummary(s);
      setTrend(t);
      setFlaky(f);
      setMatrix(m);
      setDefects(d);
      setHealth(h);
      setOverview(o);
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

  // Mapa de Risco tem janela própria (git churn, não o filtro de dias da QA)
  // e depende de subprocess — evita atrelar ao load() geral.
  useEffect(() => {
    api
      .riskMap()
      .then(setRiskMap)
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [onError]);

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

      <ExecutivePanel overview={overview} onNavigate={onNavigate} />

      <HealthScoreCard health={health} />

      {summary && (
        <div className="metric-cards">
          <MetricCard label="Cobertura de requisito" metric={summary.requirement_coverage} />
          <MetricCard label="Cobertura de execução" metric={summary.execution_coverage} />
          <MetricCard
            label="Pass rate"
            metric={summary.pass_rate}
            delta={overview?.pass_rate_trend.delta ?? null}
          />
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

      <h3 className="section-title">Mapa de Risco ({riskMap?.since_days ?? 90} dias)</h3>
      <RiskMapPanel data={riskMap} />

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

const HEALTH_COMPONENT_LABEL: Record<string, string> = {
  coverage: "Cobertura",
  defects: "Defeitos",
  automation: "Automação",
  debt: "Dívida de testes",
};

function healthLevel(score: number | null): string {
  if (score === null) return "none";
  if (score >= 80) return "ok";
  if (score >= 60) return "warn";
  return "bad";
}

/**
 * Nota única 0-100 (doc de ideias, item 9) — cada componente cita a própria
 * fórmula (tooltip), nada fica escondido atrás do número só. Pesos vêm de
 * `arbites.yaml` (`health_score.weights`), configuráveis por quem usa.
 */
function HealthScoreCard({ health }: { health: HealthScore | null }) {
  if (!health) return null;
  const level = healthLevel(health.score);
  return (
    <div className={`chart-card health-score-card health-${level}`} style={{ marginBottom: 16 }}>
      <div className="health-score-main">
        <div className="health-score-value">{health.score === null ? "—" : health.score}</div>
        <div>
          <div className="health-score-title">Health Score</div>
          <div className="caption muted">
            {health.score === null
              ? "sem dado suficiente ainda"
              : "nota composta — veja o detalhamento por componente"}
          </div>
        </div>
      </div>
      <div className="health-score-components">
        {Object.entries(health.components).map(([key, c]) => (
          <div key={key} className="health-component" title={c.formula}>
            <div className="caption muted">
              {HEALTH_COMPONENT_LABEL[key] ?? key} · peso {Math.round(c.weight * 100)}%
            </div>
            <div className="health-component-value">{c.value === null ? "—" : `${c.value}%`}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const ALERT_DOT: Record<string, string> = {
  bad: "dot-col-failed",
  warn: "dot-col-blocked",
  info: "dot-col-pending",
};

function reindexLabel(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

/**
 * Painel executivo (design-system / reporting 0063): responde "estamos
 * entregando bem? onde está o risco? o que piorou?" — alertas de risco,
 * ações recomendadas e top problemas, tudo derivado dos reports existentes.
 */
function ExecutivePanel({
  overview,
  onNavigate,
}: {
  overview: DashboardOverview | null;
  onNavigate?: (id: string) => void;
}) {
  if (!overview) return null;
  const { alerts, recommended_actions, top_problems } = overview;
  const tp = top_problems;
  const hasTopProblems =
    tp.worst_repos.length > 0 ||
    tp.top_failing_testcases.length > 0 ||
    tp.oldest_defects.length > 0;

  return (
    <div className="exec-panel block">
      <div className="exec-head">
        <h3 className="section-title" style={{ margin: 0 }}>
          Visão executiva
        </h3>
        <span className="spacer" style={{ flex: 1 }} />
        <span className="caption muted">dados de {reindexLabel(overview.last_reindex)}</span>
      </div>

      {alerts.length === 0 && recommended_actions.length === 0 ? (
        <p className="caption muted">Nenhum alerta de risco no momento.</p>
      ) : (
        <div className="exec-grid">
          <div className="exec-col">
            <h4 className="exec-col-title">Alertas de risco ({alerts.length})</h4>
            {alerts.length === 0 ? (
              <p className="caption muted">Sem alertas críticos.</p>
            ) : (
              alerts.map((a, i) => (
                <div key={i} className="exec-item">
                  <span className={`status-dot ${ALERT_DOT[a.severity]}`} />
                  <span className="exec-item-msg">{a.message}</span>
                  {a.ref && onNavigate && (
                    <button
                      type="button"
                      className="link-chip mono link-chip-btn"
                      onClick={() => onNavigate(a.ref!)}
                    >
                      {a.ref}
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="exec-col">
            <h4 className="exec-col-title">Ações recomendadas</h4>
            {recommended_actions.length === 0 ? (
              <p className="caption muted">Nada pendente.</p>
            ) : (
              recommended_actions.map((a, i) => (
                <div key={i} className="exec-item">
                  <span className="exec-item-action">→</span>
                  <span className="exec-item-msg">{a.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {hasTopProblems && (
        <div className="exec-top">
          <h4 className="exec-col-title">Top problemas</h4>
          <div className="exec-grid">
            {tp.oldest_defects.length > 0 && (
              <div className="exec-col">
                <span className="caption muted">Defeitos mais antigos</span>
                {tp.oldest_defects.map((d) => (
                  <div key={d.id} className="exec-item">
                    <button
                      type="button"
                      className="link-chip mono link-chip-btn"
                      onClick={() => onNavigate?.(d.id)}
                    >
                      {d.id}
                    </button>
                    <span className="exec-item-msg">{d.title}</span>
                    <span className="caption muted">{d.age_days}d</span>
                  </div>
                ))}
              </div>
            )}
            {tp.worst_repos.length > 0 && (
              <div className="exec-col">
                <span className="caption muted">Piores repositórios (automação)</span>
                {tp.worst_repos.map((r) => (
                  <div key={r.repo} className="exec-item">
                    <span className="mono">{r.repo}</span>
                    <span className="caption muted">
                      {r.failed} falha{r.failed === 1 ? "" : "s"}/{r.runs}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {tp.top_failing_testcases.length > 0 && (
              <div className="exec-col">
                <span className="caption muted">CTs que mais falham</span>
                {tp.top_failing_testcases.map((c) => (
                  <div key={c.testcase_id} className="exec-item">
                    <button
                      type="button"
                      className="link-chip mono link-chip-btn"
                      onClick={() => onNavigate?.(c.testcase_id)}
                    >
                      {c.testcase_id}
                    </button>
                    <span className="caption muted">{c.failed} falhas</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  metric,
  delta,
}: {
  label: string;
  metric: MetricValue;
  delta?: number | null;
}) {
  const pct = metric.value === null ? "—" : `${Math.round(metric.value * 100)}%`;
  const status = metric.status ?? "none";
  const goal =
    status !== "none" && metric.threshold?.warn !== undefined
      ? `meta ${metric.threshold.direction === "down" ? "≤" : "≥"} ${Math.round(
          (metric.threshold.warn ?? 0) * 100,
        )}%`
      : null;
  // variação vs período anterior (só quando há dado nos dois lados)
  const deltaPts =
    delta === null || delta === undefined ? null : Math.round(delta * 100);
  return (
    <div className={`metric-card metric-${status}`}>
      <div className="metric-label">
        {label}
        {status !== "none" && <span className={`metric-flag flag-${status}`} title={goal ?? ""} />}
      </div>
      <div className="metric-value">
        {pct}
        {deltaPts !== null && deltaPts !== 0 && (
          <span
            className={`metric-delta ${deltaPts > 0 ? "delta-up" : "delta-down"}`}
            title="vs. período anterior"
          >
            {deltaPts > 0 ? "▲" : "▼"} {Math.abs(deltaPts)} pts
          </span>
        )}
      </div>
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

/** Nível de risco 0–4 pelo churn do arquivo vs. o máximo do repo (estilo GitHub). */
function riskLevel(churn: number, max: number): number {
  if (churn <= 0 || max <= 0) return 0;
  const q = churn / max;
  if (q > 0.75) return 4;
  if (q > 0.5) return 3;
  if (q > 0.25) return 2;
  return 1;
}

function RiskMapPanel({ data }: { data: RiskMap | null }) {
  if (!data) return null;
  if (data.repos.length === 0) {
    return (
      <div className="empty-state block">
        <div className="empty-title">Nenhum repositório configurado</div>
        <div className="empty-body">
          Configure <span className="mono">risk_repos</span> (nome + caminho
          local) em <span className="mono">arbites.yaml</span> para ver onde
          o código muda mais, quebra mais e é menos testado.
        </div>
      </div>
    );
  }
  return (
    <div className="chart-card">
      {data.repos.map((repo) => {
        const maxChurn = Math.max(0, ...repo.files.map((f: RiskMapFile) => f.churn));
        return (
          <div key={repo.repo} className="risk-map-repo">
            <div className="defects-summary">
              <span className="mono">{repo.repo}</span>
              {repo.error ? (
                <span className="status-dot dot-col-failed caption">{repo.error}</span>
              ) : (
                <>
                  <span className="caption muted">{repo.total_commits} commits</span>
                  <span className="caption muted">
                    pass rate: {pct(repo.automation_pass_rate)}
                  </span>
                </>
              )}
            </div>
            {repo.files.length > 0 && (
              <div className="risk-map-grid">
                {repo.files.map((f) => (
                  <span
                    key={f.path}
                    className={`risk-map-cell risk-heat-${riskLevel(f.churn, maxChurn)} ${
                      f.defect_commits > 0 ? "has-defect" : ""
                    }`}
                    title={`${f.path} — ${f.churn} mudança${f.churn === 1 ? "" : "s"}${
                      f.defect_commits > 0
                        ? `, ${f.defect_commits} ligada${f.defect_commits === 1 ? "" : "s"} a defeito`
                        : ""
                    }`}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
      <div className="heatmap-legend caption muted">
        <span>menos mudanças</span>
        {[0, 1, 2, 3, 4].map((l) => (
          <span key={l} className={`risk-map-cell risk-heat-${l}`} />
        ))}
        <span>mais mudanças</span>
        <span style={{ marginLeft: 12 }} className="risk-map-cell has-defect risk-heat-0" />
        <span>commit ligado a defeito</span>
      </div>
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
